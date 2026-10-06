import Foundation
import EventKit

struct CalendarSyncResult: Sendable, Equatable {
    let addedCount: Int
    let calendarTitle: String
    let isNewCalendar: Bool

    init(addedCount: Int, calendarTitle: String, isNewCalendar: Bool) {
        self.addedCount = addedCount
        self.calendarTitle = calendarTitle
        self.isNewCalendar = isNewCalendar
    }
}

protocol CalendarExporting: Sendable {
    func generateIcsString(plan: Plan, workouts: [Workout], timePref: String) -> String
    func exportToTemporaryIcsFile(plan: Plan, workouts: [Workout], timePref: String) throws -> URL
    func syncToAppleCalendar(plan: Plan, workouts: [Workout], timePref: String) async throws -> CalendarSyncResult
}

/// Native RFC 5545 iCalendar generation and EventKit integration for Uphill AI training plans.
final class CalendarExportManager: CalendarExporting, @unchecked Sendable {
    static let shared = CalendarExportManager()

    private let eventStore: EKEventStore

    init(eventStore: EKEventStore = EKEventStore()) {
        self.eventStore = eventStore
    }

    // MARK: - RFC 5545 Text Escaping & Folding

    static func escapeText(_ val: String) -> String {
        guard !val.isEmpty else { return "" }
        var result = val.replacingOccurrences(of: "\r\n", with: "\n")
        result = result.replacingOccurrences(of: "\\", with: "\\\\")
        result = result.replacingOccurrences(of: ";", with: "\\;")
        result = result.replacingOccurrences(of: ",", with: "\\,")
        result = result.replacingOccurrences(of: "\n", with: "\\n")
        return result
    }

    static func foldLine(_ line: String) -> String {
        guard !line.isEmpty else { return "" }
        var chunks: [String] = []
        var currentChunk = ""
        var currentBytes = 0
        let limit = 75

        for char in line {
            let charBytes = String(char).utf8.count
            if currentBytes + charBytes > limit {
                chunks.append(currentChunk)
                currentChunk = " " + String(char)
                currentBytes = 1 + charBytes
            } else {
                currentChunk.append(String(char))
                currentBytes += charBytes
            }
        }

        if !currentChunk.isEmpty {
            chunks.append(currentChunk)
        }

        return chunks.joined(separator: "\r\n")
    }

    // MARK: - ICS String Generation

    func generateIcsString(plan: Plan, workouts: [Workout], timePref: String = "all_day") -> String {
        let utcFormatter = ISO8601DateFormatter()
        utcFormatter.formatOptions = [.withYear, .withMonth, .withDay, .withTime]
        let timestamp = utcFormatter.string(from: Date()).replacingOccurrences(of: "-", with: "").replacingOccurrences(of: ":", with: "") + "Z"

        var icsLines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Uphill AI//Workout Scheduler//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]

        let calendar = PlanCalendar.calendar

        for (idx, wo) in workouts.enumerated() {
            guard let workoutDate = PlanCalendar.date(
                week: wo.weekNumber,
                weekday: wo.weekday,
                plan: plan,
                workouts: workouts,
                calendar: calendar
            ) else {
                continue
            }

            let uid = "uphill-ai-wo-\(wo.planId)-\(wo.weekNumber)-\(wo.weekday.offset)-\(wo.id)-\(idx)@uphill.ai"
            var summary = "Uphill AI: \(wo.title)"
            if wo.isRest {
                summary += " (Rest)"
            }

            // Assemble rich description
            var descParts: [String] = []
            let dateString = workoutDate.formatted(date: .complete, time: .omitted)
            descParts.append("Scheduled Date: \(dateString)")
            descParts.append("Phase: \(wo.phase)")
            descParts.append("Type: \(wo.type)")

            if wo.durationMinutes > 0 {
                descParts.append("Duration: \(Int(wo.durationMinutes)) mins")
            }
            if let km = wo.distanceKm, km > 0 {
                descParts.append(String(format: "Distance: %.1f km", km))
            }
            if let hr = wo.targetHrRange, !hr.isEmpty {
                descParts.append("HR Range: \(hr)")
            }
            if !wo.targetZone.isEmpty {
                descParts.append("Target Effort: \(wo.targetZone)")
            }
            if let pace = wo.targetPace, !pace.isEmpty {
                descParts.append("Target Pace: \(pace)")
            }
            if let inc = wo.treadmillIncline, inc != "0", let spd = wo.treadmillSpeed {
                descParts.append("Treadmill: Incline \(inc)% | Speed \(spd) kph")
            }
            if let desc = wo.description, !desc.isEmpty {
                descParts.append("\nWorkout Guide:\n\(desc)")
            }
            if let tip = wo.fuelingTip, !tip.isEmpty {
                descParts.append("\nFueling / Nutrition:\n\(tip)")
            }

            let rawDescription = descParts.joined(separator: "\n")

            icsLines.append("BEGIN:VEVENT")
            icsLines.append("UID:\(uid)")
            icsLines.append("DTSTAMP:\(timestamp)")

            if timePref == "morning" || timePref == "afternoon" || timePref == "evening" {
                let startHour: Int = (timePref == "morning") ? 6 : ((timePref == "afternoon") ? 14 : 18)
                let durationMinutes = max(45, Int(wo.durationMinutes > 0 ? wo.durationMinutes : 60))

                var startComponents = calendar.dateComponents([.year, .month, .day], from: workoutDate)
                startComponents.hour = startHour
                startComponents.minute = 0
                startComponents.second = 0

                let startDt = calendar.date(from: startComponents) ?? workoutDate
                let endDt = calendar.date(byAdding: .minute, value: durationMinutes, to: startDt) ?? startDt

                let dtFormatter = DateFormatter()
                dtFormatter.dateFormat = "yyyyMMdd'T'HHmmss"
                dtFormatter.timeZone = calendar.timeZone

                let startStr = dtFormatter.string(from: startDt)
                let endStr = dtFormatter.string(from: endDt)

                icsLines.append("DTSTART:\(startStr)")
                icsLines.append("DTEND:\(endStr)")
            } else {
                // All-day event per RFC 5545: DTEND is non-inclusive (the following day)
                let dateStr = PlanCalendar.ymd(workoutDate, calendar: calendar).replacingOccurrences(of: "-", with: "")
                let nextDay = calendar.date(byAdding: .day, value: 1, to: workoutDate) ?? workoutDate
                let nextDateStr = PlanCalendar.ymd(nextDay, calendar: calendar).replacingOccurrences(of: "-", with: "")

                icsLines.append("DTSTART;VALUE=DATE:\(dateStr)")
                icsLines.append("DTEND;VALUE=DATE:\(nextDateStr)")
            }

            icsLines.append("SUMMARY:\(Self.escapeText(summary))")
            icsLines.append("DESCRIPTION:\(Self.escapeText(rawDescription))")
            icsLines.append("END:VEVENT")
        }

        icsLines.append("END:VCALENDAR")

        let folded = icsLines.map { Self.foldLine($0) }
        return folded.joined(separator: "\r\n") + "\r\n"
    }

    // MARK: - Temporary File Export

    func exportToTemporaryIcsFile(plan: Plan, workouts: [Workout], timePref: String = "all_day") throws -> URL {
        let icsText = generateIcsString(plan: plan, workouts: workouts, timePref: timePref)
        let tempDir = FileManager.default.temporaryDirectory
        let fileName = "uphill_plan_\(plan.id)_\(timePref).ics"
        let fileURL = tempDir.appendingPathComponent(fileName)

        guard let data = icsText.data(using: .utf8) else {
            throw NSError(domain: "CalendarExportManager", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to encode ICS as UTF-8"])
        }

        try data.write(to: fileURL, options: .atomic)
        return fileURL
    }

    // MARK: - EventKit Direct Sync

    func syncToAppleCalendar(plan: Plan, workouts: [Workout], timePref: String = "all_day") async throws -> CalendarSyncResult {
        // Request calendar write access
        let granted: Bool
        if #available(iOS 17.0, *) {
            granted = try await eventStore.requestWriteOnlyAccessToEvents()
        } else {
            granted = try await eventStore.requestAccess(to: .event)
        }

        guard granted else {
            throw NSError(domain: "CalendarExportManager", code: 403, userInfo: [
                NSLocalizedDescriptionKey: "Calendar access was denied. Please allow calendar access in Settings."
            ])
        }

        // Find or create Uphill AI Training calendar
        let calendarName = "Uphill AI Training"
        let existingCalendars = eventStore.calendars(for: .event)
        var targetCalendar = existingCalendars.first { $0.title == calendarName }
        var isNewCalendar = false

        if targetCalendar == nil {
            let newCal = EKCalendar(for: .event, eventStore: eventStore)
            newCal.title = calendarName
            newCal.cgColor = CGColor(red: 16.0 / 255.0, green: 185.0 / 255.0, blue: 129.0 / 255.0, alpha: 1.0)

            let sources = eventStore.sources
            if let defaultSource = eventStore.defaultCalendarForNewEvents?.source {
                newCal.source = defaultSource
            } else if let calDav = sources.first(where: { $0.sourceType == .calDAV }) {
                newCal.source = calDav
            } else if let local = sources.first(where: { $0.sourceType == .local }) {
                newCal.source = local
            } else if let first = sources.first {
                newCal.source = first
            }

            try eventStore.saveCalendar(newCal, commit: true)
            targetCalendar = newCal
            isNewCalendar = true
        }

        guard let targetCalendar else {
            throw NSError(domain: "CalendarExportManager", code: 500, userInfo: [
                NSLocalizedDescriptionKey: "Could not create or locate Uphill AI Training calendar."
            ])
        }

        let calendar = PlanCalendar.calendar
        var addedCount = 0

        for wo in workouts {
            guard let workoutDate = PlanCalendar.date(
                week: wo.weekNumber,
                weekday: wo.weekday,
                plan: plan,
                workouts: workouts,
                calendar: calendar
            ) else {
                continue
            }

            let event = EKEvent(eventStore: eventStore)
            event.calendar = targetCalendar

            var title = "Uphill AI: \(wo.title)"
            if wo.isRest {
                title += " (Rest)"
            }
            event.title = title

            var descParts: [String] = []
            descParts.append("Phase: \(wo.phase)")
            descParts.append("Type: \(wo.type)")
            if wo.durationMinutes > 0 {
                descParts.append("Duration: \(Int(wo.durationMinutes)) mins")
            }
            if let km = wo.distanceKm, km > 0 {
                descParts.append(String(format: "Distance: %.1f km", km))
            }
            if let hr = wo.targetHrRange, !hr.isEmpty {
                descParts.append("HR: \(hr)")
            }
            if !wo.targetZone.isEmpty {
                descParts.append("Zone: \(wo.targetZone)")
            }
            if let desc = wo.description, !desc.isEmpty {
                descParts.append("\n\(desc)")
            }
            if let tip = wo.fuelingTip, !tip.isEmpty {
                descParts.append("\nFueling: \(tip)")
            }
            event.notes = descParts.joined(separator: "\n")

            if timePref == "morning" || timePref == "afternoon" || timePref == "evening" {
                let startHour = (timePref == "morning") ? 6 : ((timePref == "afternoon") ? 14 : 18)
                let durationMinutes = max(45, Int(wo.durationMinutes > 0 ? wo.durationMinutes : 60))

                var startComponents = calendar.dateComponents([.year, .month, .day], from: workoutDate)
                startComponents.hour = startHour
                startComponents.minute = 0
                startComponents.second = 0

                let startDt = calendar.date(from: startComponents) ?? workoutDate
                let endDt = calendar.date(byAdding: .minute, value: durationMinutes, to: startDt) ?? startDt

                event.startDate = startDt
                event.endDate = endDt
                event.isAllDay = false
            } else {
                event.startDate = calendar.startOfDay(for: workoutDate)
                event.endDate = calendar.date(byAdding: .day, value: 1, to: event.startDate) ?? event.startDate
                event.isAllDay = true
            }

            try eventStore.save(event, span: .thisEvent, commit: false)
            addedCount += 1
        }

        try eventStore.commit()

        return CalendarSyncResult(
            addedCount: addedCount,
            calendarTitle: targetCalendar.title,
            isNewCalendar: isNewCalendar
        )
    }
}
