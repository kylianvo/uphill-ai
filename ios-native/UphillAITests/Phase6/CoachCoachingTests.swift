import Testing
import Foundation
@testable import UphillAI

@Suite("CoachCoachingTests")
struct CoachCoachingTests {

    @Test func testWorkoutTypeOptions() {
        #expect(CoachWorkoutTypeOption.all.count == 10)
        let easy = CoachWorkoutTypeOption.find("Easy")
        #expect(easy != nil)
        #expect(easy?.labelEn == "Easy")

        let tempo = CoachWorkoutTypeOption.find("Tempo")
        #expect(tempo != nil)
        #expect(tempo?.labelVi == "Tempo")

        let me = CoachWorkoutTypeOption.find("Muscular Endurance")
        #expect(me != nil)
        #expect(me?.labelVi == "Muscular Endurance (ME)")

        let unknown = CoachWorkoutTypeOption.find("NonExistent")
        #expect(unknown == nil)
    }

    @Test func testCoachOverviewDecoding() throws {
        let json = """
        {
            "athletes": [
                {
                    "athlete_id": 42,
                    "name": "Minh Tran",
                    "runner_level": "intermediate",
                    "needs_attention": false,
                    "adherence_pct": 94.0,
                    "missed_streak": 0,
                    "active_plan": {
                        "plan_id": 101,
                        "race_name": "Dalat Ultra Trail 50K",
                        "race_date": "2026-11-15",
                        "current_week": 6,
                        "total_weeks": 16
                    },
                    "last_completed": {
                        "week_number": 6,
                        "day_of_week": "Sunday"
                    }
                }
            ],
            "action_items": {
                "draft_plans": [
                    {
                        "plan_id": 105,
                        "athlete_id": 55,
                        "athlete_name": "Huy Le",
                        "race_name": "Vietnam Mountain Marathon 70K"
                    }
                ],
                "pending_workout_approvals": [
                    {
                        "workout_id": 301,
                        "plan_id": 101,
                        "athlete_id": 42,
                        "athlete_name": "Minh Tran",
                        "title": "Hill Intervals 8x3min"
                    }
                ]
            },
            "phase_alerts": [
                {
                    "athlete_id": 42,
                    "athlete_name": "Minh Tran",
                    "phase": "Taper",
                    "starts": "2026-10-25"
                }
            ],
            "workout_type_mix": [
                { "type": "Easy", "count": 28, "pct": 45.0 },
                { "type": "Long Run", "count": 16, "pct": 25.0 }
            ],
            "adherence_trend": [
                { "week_number": 1, "adherence_pct": 82.0 },
                { "week_number": 2, "adherence_pct": 88.5 }
            ],
            "missed_by_day": [
                { "day_of_week": "Mon", "count": 1 },
                { "day_of_week": "Wed", "count": 2 }
            ],
            "races": [
                {
                    "race_name": "Dalat Ultra Trail 50K",
                    "race_date": "2026-11-15",
                    "count": 1,
                    "athletes": [
                        { "athlete_id": 42, "name": "Minh Tran" }
                    ]
                }
            ],
            "roster_totals": {
                "distance_km": 420.5,
                "duration_hours": 38.5,
                "elevation_gain_m": 12500,
                "workout_count": 48
            },
            "athletes_without_race": 1
        }
        """.data(using: .utf8)!

        let overview = try JSONCoding.decoder.decode(CoachOverview.self, from: json)
        #expect(overview.athletes.count == 1)
        #expect(overview.athletes.first?.name == "Minh Tran")
        #expect(overview.actionItems.draftPlans.count == 1)
        #expect(overview.actionItems.pendingWorkoutApprovals.count == 1)
        #expect(overview.phaseAlerts.count == 1)
        #expect(overview.phaseAlerts.first?.phase == "Taper")
        #expect(overview.workoutTypeMix.count == 2)
        #expect(overview.adherenceTrend.count == 2)
        #expect(overview.missedByDay.count == 2)
        #expect(overview.races.count == 1)
        #expect(overview.rosterTotals?.workoutCount == 48)
        #expect(overview.athletesWithoutRace == 1)
    }

    @Test func testCoachRosterDecoding() throws {
        let json = """
        [
            {
                "id": 10,
                "athlete_id": 42,
                "athlete_name": "Minh Tran",
                "athlete_email": "minh@example.com",
                "status": "active",
                "invited_at": "2026-09-01T10:00:00Z",
                "responded_at": "2026-09-02T11:00:00Z"
            },
            {
                "id": 11,
                "athlete_id": 99,
                "athlete_name": null,
                "athlete_email": "runner@test.com",
                "status": "invited",
                "invited_at": "2026-10-05T12:00:00Z",
                "responded_at": null
            }
        ]
        """.data(using: .utf8)!

        let roster = try JSONCoding.decoder.decode([CoachedAthleteRow].self, from: json)
        #expect(roster.count == 2)
        #expect(roster[0].isActive == true)
        #expect(roster[0].displayName == "Minh Tran")
        #expect(roster[1].isActive == false)
        #expect(roster[1].displayName == "runner@test.com")
    }

    @Test func testCoachNotesDecoding() throws {
        let json = """
        {
            "notes": [
                {
                    "id": 1,
                    "coach_id": 7,
                    "athlete_id": 42,
                    "target_type": "workout",
                    "target_id": 301,
                    "note": "Keep cadence above 175 spm on the uphill segments.",
                    "created_at": "2026-10-05T14:00:00Z"
                },
                {
                    "id": 2,
                    "coach_id": 7,
                    "athlete_id": 42,
                    "target_type": "workout",
                    "target_id": 301,
                    "note": "Understood coach! Will focus on quick steps.",
                    "created_at": "2026-10-05T15:30:00Z"
                }
            ]
        }
        """.data(using: .utf8)!

        let res = try JSONCoding.decoder.decode(CoachNotesResponse.self, from: json)
        #expect(res.notes.count == 2)
        #expect(res.notes[0].coachId == 7)
        #expect(res.notes[0].targetType == "workout")
        #expect(res.notes[1].note.contains("Understood"))
    }

    @Test func testCoachingServiceAPI() async throws {
        let client = makeStubClient { request in
            let url = request.url?.absoluteString ?? ""
            if url.contains("/api/coaching/roster") {
                let rosterJson = """
                [
                    {
                        "id": 1,
                        "athlete_id": 100,
                        "athlete_name": "Test Runner",
                        "athlete_email": "test@uphill.ai",
                        "status": "active",
                        "invited_at": "2026-09-01T00:00:00Z",
                        "responded_at": "2026-09-02T00:00:00Z"
                    }
                ]
                """
                return (200, rosterJson.data(using: .utf8)!)
            } else if url.contains("/api/coaching/my-invites") {
                let invitesJson = """
                [
                    {
                        "id": 5,
                        "coach_id": 7,
                        "coach_name": "Coach Kylian",
                        "coach_email": "kylian@uphill.ai",
                        "status": "pending",
                        "invited_at": "2026-10-01T10:00:00Z"
                    }
                ]
                """
                return (200, invitesJson.data(using: .utf8)!)
            } else if url.contains("/approve") {
                let wJson = """
                {
                    "id": 301,
                    "plan_id": 50,
                    "week_number": 1,
                    "day_of_week": "Monday",
                    "phase": "Build",
                    "title": "Approved Run",
                    "type": "Easy",
                    "duration_minutes": 45,
                    "target_zone": "Zone 2",
                    "approved_at": "2026-10-06T00:00:00Z"
                }
                """
                return (200, wJson.data(using: .utf8)!)
            } else {
                return (200, Data())
            }
        }

        let service = CoachingService(client: client)
        let roster = try await service.fetchRoster()
        #expect(roster.count == 1)
        #expect(roster.first?.athleteName == "Test Runner")

        let invites = try await service.fetchMyInvites()
        #expect(invites.count == 1)
        #expect(invites.first?.displayCoachName == "Coach Kylian")

        let approved = try await service.approveWorkout(athleteId: 100, planId: 50, workoutId: 301)
        #expect(approved.approvedAt != nil)
        #expect(approved.title == "Approved Run")
    }
}
