import SwiftUI

struct WatchZonesGuideSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var method = 0
    init(method: Int = 0) { _method = State(initialValue: method) }

    var body: some View {
        NavigationStack {
            List {
                Picker("Find your values", selection: $method) {
                    Text("From watch").tag(0)
                    Text("Field test").tag(1)
                }
                .pickerStyle(.segmented)
                Section("Heart Rate Spectrum") {
                    TrainingZoneBar()
                }
                if method == 0 {
                    Section {
                        Text("Watch zones are estimates unless calibrated by a test. Zone numbers vary by zone model; a percentage of Max HR is not a measured AeT or AnT.")
                    }

                    Section("Aerobic Threshold (AeT)") {
                        Text("Upper limit of Zone 2 (Easy). Conversational effort, key aerobic base for ultra trail endurance.")
                    }
                    Section("Anaerobic Threshold (AnT)") {
                        Text("Use a tested Lactate Threshold (LTHR) when available. Do not assume every watch Zone 4 boundary is AnT.")
                    }
                    Section("Garmin") {
                        Text("Open Garmin Connect app on your phone.")
                        Text("Tap More (...) > Settings > User Settings.")
                        Text("Select Heart Rate & Power Zones > Heart Rate > Zones.")
                        Text("Copy your tested thresholds if available, or use watch zone boundaries as estimates.")
                    }
                    Section("COROS") {
                        Text("Open the COROS app on your phone.")
                        Text("Go to Profile tab (bottom right) > Settings > Heart Rate Zone.")
                        Text("Select Threshold Heart Rate Zone (or Max HR Zone).")
                        Text("Check your Aerobic Endurance limit and threshold heart rate. Keep watch-generated values marked as estimates.")
                    }
                    Section("Apple Watch") {
                        Text("Open the Apple Watch app on your iPhone.")
                        Text("Scroll down and tap Workout.")
                        Text("Tap Heart Rate Zones (calculated automatically or manual).")
                        Text("Automatic zones use a heart rate formula. Treat their boundaries as estimates, not measured thresholds.")
                    }
                    Section("Suunto / Polar / Strava") {
                        Text("Suunto: Suunto App > Profile > Watch Settings > Intensity Zones.")
                        Text("Polar: Polar Flow App > Sport Profiles > Heart Rate Zones.")
                        Text("Strava: You > Settings > Heart Rate > Max & Custom Zones.")
                    }
                    Section("Running pace (min/km)") {
                        Text("Look for running Lactate Threshold pace in Garmin Connect or Threshold Pace in COROS EvoLab, if available. Use easy runs on flat ground for your easy pace range. Convert min/mile values to min/km before entering them.")
                    }
                } else {
                    Section("Aerobic Threshold (AeT)") {
                        Text("Warm up, then hold a steady speed for 60 minutes. Compare heart rate between halves; drift above 5% suggests you started above AeT. Follow Evoke's full protocol and interpretation.")
                    }
                    Section("Anaerobic Threshold (AnT)") {
                        Text("Evoke uses a sustained 20–60 minute time trial, depending on experience. Average heart rate estimates AnT for that activity. This is a hard effort; test well-rested.")
                    }
                    Section("Running pace (min/km)") {
                        Text("Record easy pace below AeT on flat ground. Use a flat running time trial for Threshold pace; uphill pace is not interchangeable.")
                    }
                    Section {
                        Link("Read Evoke's assessment guide", destination: URL(string: "https://evokeendurance.com/resources/our-latest-thinking-on-aerobic-assessment-for-the-mountain-athlete/")!)
                        Text("You can skip these fields and add test results later.")
                    }
                }
            }
            .navigationTitle("Training zones guide")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Got it") { dismiss() } }
        }
    }
}
