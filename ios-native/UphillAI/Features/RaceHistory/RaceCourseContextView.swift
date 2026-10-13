import SwiftUI

struct RaceCourseContextView: View {
    let context: RaceCourseContext
    let resultYear: String
    let onChoose: (Int) -> Void
    let onRetry: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            if let course = context.course {
                Text(course.raceName).font(UH.TextStyle.label)
                if course.editionStatus == "different", let year = course.editionYear {
                    Text("Course profile: \(String(year)); your result: \(resultYear)").foregroundStyle(UH.Palette.secondary)
                } else if course.editionStatus == "unknown" {
                    Text("Course edition not recorded").foregroundStyle(UH.Palette.secondary)
                }
                Text("\(course.distanceLabel) · Course context").font(UH.TextStyle.caption)
                if let location = course.location { Label(location, systemImage: "mappin.and.ellipse") }
                if let elevation = course.elevationGainM { Text("Course elevation gain: \(RaceDisplay.number(elevation)) m") }
                facts("Terrain", values: course.terrain)
                facts("Key climbs", values: course.keyClimbs)
                if !course.climate.isEmpty {
                    Text("Typical conditions").font(UH.TextStyle.label)
                    if let temperature = course.climate["avg_temp_c"]?.doubleValue { Text("Average temperature: \(RaceDisplay.number(temperature)) °C") }
                    if let humidity = course.climate["humidity_pct"] {
                        if let value = humidity.stringValue { Text("Humidity: \(value)") }
                        else if let value = humidity.doubleValue { Text("Humidity: \(RaceDisplay.number(value))%") }
                    }
                    if let season = course.climate["season"]?.stringValue { Text(season) }
                    if let notes = course.climate["notes"]?.stringValue { Text(notes) }
                }
                facts("Runner reviews", values: course.runnerReviews)
                if let label = course.sourceLabel { Text("Source: \(label)").font(UH.TextStyle.caption) }
                if let date = course.verifiedAt { Text("Verified: \(date)").font(UH.TextStyle.caption) }
                ForEach(course.sourceUrls, id: \.self) { source in
                    if let url = safeRaceResultURL(source) { Link("Course source · \(url.host ?? "Website")", destination: url) }
                }
            } else if context.status == "ambiguous" {
                Text("Choose the course for this review. Your race record stays the same.")
                ForEach(context.candidates) { candidate in
                    Button("\(candidate.raceName) · \(candidate.distanceLabel)") { onChoose(candidate.id) }
                        .frame(minHeight: 44).multilineTextAlignment(.leading)
                }
            } else if context.status == "unavailable" {
                Text(context.message ?? "Course context could not be loaded.")
                Button("Retry", action: onRetry)
            } else { Text("No course context available").foregroundStyle(UH.Palette.secondary) }
        }.font(UH.TextStyle.body)
    }
    @ViewBuilder private func facts(_ heading: String, values: [String]) -> some View {
        if !values.isEmpty {
            Text(heading).font(UH.TextStyle.label)
            ForEach(Array(values.enumerated()), id: \.offset) { _, value in Text(value) }
        }
    }
}
