import SwiftUI

struct WatchZonesGuideSheet: View {
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            List {
                Section("Aerobic Threshold (AeT)") {
                    Text("Upper limit of Zone 2 (Easy). Conversational effort, key aerobic base for ultra trail endurance.")
                }
                Section("Anaerobic Threshold (AnT)") {
                    Text("Upper limit of Zone 4 / Lactate Threshold (LTHR). Maximum effort sustainable for ~1 hour.")
                }
                Section("Garmin") {
                    Text("Open Garmin Connect app on your phone.")
                    Text("Tap More (...) > Settings > User Settings.")
                    Text("Select Heart Rate & Power Zones > Heart Rate > Zones.")
                    Text("Note your Zone 2 upper limit (AeT) and Zone 4 upper limit / Lactate Threshold (AnT).")
                }
                Section("COROS") {
                    Text("Open the COROS app on your phone.")
                    Text("Go to Profile tab (bottom right) > Settings > Heart Rate Zone.")
                    Text("Select Threshold Heart Rate Zone (or Max HR Zone).")
                    Text("Your Aerobic Endurance upper limit is AeT; your Threshold zone limit is AnT.")
                }
                Section("Apple Watch") {
                    Text("Open the Apple Watch app on your iPhone.")
                    Text("Scroll down and tap Workout.")
                    Text("Tap Heart Rate Zones (calculated automatically or manual).")
                    Text("Zone 2 upper limit is AeT; Zone 4 upper limit is AnT.")
                }
                Section("Suunto / Polar / Strava") {
                    Text("Suunto: Suunto App > Profile > Watch Settings > Intensity Zones.")
                    Text("Polar: Polar Flow App > Sport Profiles > Heart Rate Zones.")
                    Text("Strava: You > Settings > Heart Rate > Max & Custom Zones.")
                }
            }.navigationTitle("How to Find Your Heart Rate Zones & Thresholds")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Got it") { dismiss() } }
        }
    }
}
