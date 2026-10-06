import Foundation
import Testing
@testable import UphillAI

@MainActor
struct ProfileSettingsTests {
    @Test func changingOneHeartRatePreservesRequiredProfileFields() throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        var draft = ProfileDraft(user: user)
        draft.aetHr = 138
        let body = draft.body(merging: user, section: .heartRate)
        #expect(body.age == user.age)
        #expect(body.maxHr == user.maxHr)
        #expect(body.restingHr == user.restingHr)
        #expect(body.aetHr == 138)
        #expect(body.antHr == user.antHr)
        #expect(body.weightKg == user.weightKg)
        let data = try JSONCoding.encoder.encode(body)
        #expect(!String(decoding: data, as: UTF8.self).contains("gemini_api_key"))
    }

    @Test func heartRateOrderingRejectsInvalidThresholds() throws {
        var draft = ProfileDraft(user: try Fixture.decode(User.self, "auth_me.json"))
        draft.aetHr = draft.antHr
        #expect(draft.heartRateError != nil)
        draft.aetHr = 140
        draft.antHr = 165
        draft.maxHr = 160
        #expect(draft.heartRateError != nil)
        draft.maxHr = 185
        draft.restingHr = 140
        #expect(draft.heartRateError != nil)
        draft.restingHr = 60
        #expect(draft.heartRateError == nil)
    }

    @Test func offlineSaveDoesNotCallNetwork() async throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        session.setUser(user)
        let client = makeStubClient { _ in
            Issue.record("Offline save must not send a request")
            return (500, json([:]))
        }
        let model = ProfileSettingsModel(user: user, section: .aboutYou, service: ProfileService(client: client), session: session, isOffline: { true })
        await model.save()
        #expect(model.error == PlanViewModel.offlineMessage)
        #expect(session.user == user)
    }

    @Test func decodesRecordedProfileAndZones() throws {
        let user = try Fixture.decode(User.self, "update_profile.json")
        let zones = try Fixture.decode(PaceZones.self, "pace_zones.json")
        #expect(user.aetHr != nil)
        #expect(zones.rows.count == 5)
    }
    @Test func changingTrainingZonesPreservesAndUpdatesBothHeartRateAndPaceFields() throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        var draft = ProfileDraft(user: user)
        draft.aetHr = 138
        draft.thresholdPace = "4:45"
        let body = draft.body(merging: user, section: .trainingZones)
        #expect(body.age == user.age)
        #expect(body.aetHr == 138)
        #expect(body.thresholdPace == "4:45")
    }
}
