import XCTest
@testable import UphillAI

final class RaceDisplayTests: XCTestCase {
    func testPaceRoundsOnceBeforeSplitting() {
        XCTAssertEqual(RaceDisplay.pace(359.5), "6:00")
        XCTAssertEqual(RaceDisplay.pace(359.4), "5:59")
    }
    func testNumbersFollowAppLanguage() {
        XCTAssertEqual(RaceDisplay.number(1234.5, vietnamese: false), "1,234.5")
        XCTAssertEqual(RaceDisplay.number(1234.5, vietnamese: true), "1.234,5")
        XCTAssertEqual(RaceDisplay.number(50, vietnamese: false), "50")
    }
    func testLocalizedLabels() {
        XCTAssertEqual(RaceDisplay.discipline("road", vietnamese: true), "Road")
        XCTAssertEqual(RaceDisplay.discipline("trail", vietnamese: false), "Trail")
        XCTAssertEqual(RaceDisplay.source("manual", vietnamese: true), "Tự nhập")
        XCTAssertEqual(RaceDisplay.source("manual", vietnamese: false), "Manual entry")
        XCTAssertEqual(RaceDisplay.source("vbm", vietnamese: false), "VBM")
        XCTAssertEqual(RaceDisplay.source("utmb", vietnamese: true), "UTMB")
    }
    func testTrailingDateIsStripped() {
        XCTAssertEqual(RaceDisplay.stripTrailingDate("Hanoi Marathon 05/10/2025"), "Hanoi Marathon")
        XCTAssertEqual(RaceDisplay.stripTrailingDate("Hanoi Marathon (05/10/2025)"), "Hanoi Marathon")
        XCTAssertEqual(RaceDisplay.stripTrailingDate("Hanoi Marathon"), "Hanoi Marathon")
    }
}
