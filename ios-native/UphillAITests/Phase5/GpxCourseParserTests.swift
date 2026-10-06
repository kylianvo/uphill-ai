import Testing
import Foundation
@testable import UphillAI

@Suite("GpxCourseParserTests")
struct GpxCourseParserTests {

    private func makeSampleGpxXml() -> String {
        """
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Uphill AI Test">
  <wpt lat="22.3300" lon="103.8500">
    <ele>1620.0</ele>
    <name>CP1 - Cat Cat</name>
  </wpt>
  <wpt lat="22.3600" lon="103.8800">
    <ele>1850.0</ele>
    <name>CP2 - Sin Chai</name>
  </wpt>
  <trk>
    <name>Sa Pa Trail 25K</name>
    <trkseg>
      <trkpt lat="22.3000" lon="103.8200"><ele>1500.0</ele></trkpt>
      <trkpt lat="22.3100" lon="103.8300"><ele>1550.0</ele></trkpt>
      <trkpt lat="22.3200" lon="103.8400"><ele>1600.0</ele></trkpt>
      <trkpt lat="22.3300" lon="103.8500"><ele>1620.0</ele></trkpt>
      <trkpt lat="22.3400" lon="103.8600"><ele>1700.0</ele></trkpt>
      <trkpt lat="22.3500" lon="103.8700"><ele>1780.0</ele></trkpt>
      <trkpt lat="22.3600" lon="103.8800"><ele>1850.0</ele></trkpt>
      <trkpt lat="22.3700" lon="103.8900"><ele>1800.0</ele></trkpt>
      <trkpt lat="22.3800" lon="103.9000"><ele>1720.0</ele></trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    }

    @Test func testParseValidGpx() throws {
        let xml = makeSampleGpxXml()
        let data = xml.data(using: .utf8)!

        let result = try GpxCourseParser.parse(data: data, fileName: "sapa_trail_25k.gpx", intervalKm: 3.0)

        #expect(result.fileName == "sapa_trail_25k.gpx")
        #expect(result.totalDistanceKm > 5.0)
        #expect(result.totalElevationGainM > 300.0)
        #expect(result.checkpoints.count >= 2)
        #expect(result.checkpoints.first?.name == "Start")
        #expect(result.checkpoints.first?.distanceMeters == 0)
        #expect(result.checkpoints.last?.name == "Finish")
        #expect(result.trackpointCount == 9)
        #expect(result.waypointNames.contains("CP1 - Cat Cat"))
    }

    @Test func testHaversineDistance() {
        // Distance between Hanoi (21.0285, 105.8542) and Hai Phong (20.8449, 106.6881) is approx 90-105 km
        let d = GpxCourseParser.haversineMeters(lat1: 21.0285, lon1: 105.8542, lat2: 20.8449, lon2: 106.6881)
        #expect(d > 80000.0 && d < 120000.0)
    }

    @Test func testEmptyGpxThrows() {
        let emptyData = Data()
        #expect(throws: GpxParseError.self) {
            try GpxCourseParser.parse(data: emptyData, fileName: "empty.gpx")
        }
    }

    @Test func testNoTrackpointsThrows() {
        let noPointsXml = "<gpx><name>Empty</name></gpx>"
        let data = noPointsXml.data(using: .utf8)!
        #expect(throws: GpxParseError.self) {
            try GpxCourseParser.parse(data: data, fileName: "empty_track.gpx")
        }
    }
}
