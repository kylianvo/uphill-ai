import XCTest

@MainActor
final class RaceHistoryFlowUITests: XCTestCase {
    private func find(_ element: XCUIElement, in app: XCUIApplication, up: Bool = true) {
        for _ in 0..<12 {
            if element.exists && element.isHittable { return }
            if up { app.swipeUp() } else { app.swipeDown() }
        }
    }

    private func signIn(port: Int = 8014, accessibilitySize: Bool = false) async throws -> XCUIApplication {
        var request = URLRequest(url: URL(string: "http://127.0.0.1:\(port)/api/auth/login")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["email": "ios-preview@uphill.ai", "password": "uphill-preview-1"])
        let (data, response) = try await URLSession.shared.data(for: request)
        XCTAssertEqual((response as? HTTPURLResponse)?.statusCode, 200)
        let body = try XCTUnwrap(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        let token = try XCTUnwrap(body["session_token"] as? String)
        let app = XCUIApplication()
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local", "-UITEST_NO_AUTOFILL", "YES", "-UIPreferredContentSizeCategoryName", accessibilitySize ? "UICTContentSizeCategoryAccessibilityXXXL" : "UICTContentSizeCategoryL"]
        app.launchEnvironment["UPHILL_LOCAL_API_PORT"] = String(port)
        app.launchEnvironment["UITEST_SESSION_TOKEN"] = token
        app.launch()
        XCTAssertTrue(app.buttons["Me"].firstMatch.waitForExistence(timeout: 30))
        tapMe(app)
        let history = app.buttons["Race history"]
        find(history, in: app)
        XCTAssertTrue(history.exists)
        history.tap()
        return app
    }

    private func tapMe(_ app: XCUIApplication) {
        let buttons = app.buttons.matching(NSPredicate(format: "label == 'Me'"))
        for _ in 0..<4 {
            if let visible = buttons.allElementsBoundByIndex.filter({ $0.isHittable })
                .max(by: { $0.frame.maxY < $1.frame.maxY }) {
                print("Me tab candidates: \(buttons.allElementsBoundByIndex.map { $0.frame })")
                visible.tap()
                if app.staticTexts["ios-preview@uphill.ai"].waitForExistence(timeout: 3) { return }
            }
            app.swipeDown()
        }
        print(app.debugDescription)
        XCTFail("A visible Me tab should be available")
    }

    private func capture(_ app: XCUIApplication, _ name: String) throws {
        let directory = URL(filePath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appending(path: "docs/screenshots/race-history-results")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        try app.screenshot().pngRepresentation.write(to: directory.appending(path: "\(name).png"))
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways
        add(attachment)
    }

    func testReviewRetryKeepsRecordedResult() async throws {
        continueAfterFailure = false
        let app = try await signIn(port: 8015)
        let row = app.staticTexts["Preview Review Mountain Trail"].firstMatch
        find(row, in: app); row.tap()
        let retry = app.buttons["Retry"]
        find(retry, in: app)
        XCTAssertTrue(retry.waitForExistence(timeout: 10))
        try capture(app, "native-review-retry")
        retry.tap()
        let terrain = app.staticTexts["Technical singletrack"]
        find(terrain, in: app)
        XCTAssertTrue(terrain.waitForExistence(timeout: 10))
        try capture(app, "native-review-recovered")
    }

    func testRaceReviewStates() async throws {
        continueAfterFailure = false
        let app = try await signIn()
        for name in ["Preview Review Mountain Trail", "Preview Review Twin Trail", "Preview Review Unknown Wilderness", "Preview Review DNF Trail"] {
            let row = app.staticTexts[name].firstMatch
            find(row, in: app)
            XCTAssertTrue(row.exists)
            row.tap()
            let review = app.staticTexts["Race Review"]
            find(review, in: app)
            XCTAssertTrue(review.waitForExistence(timeout: 10))
            try capture(app, name.replacingOccurrences(of: " ", with: "-"))
            if name == "Preview Review Twin Trail" {
                let choice = app.buttons["Preview Review Twin Trail North · 50 km"]
                find(choice, in: app); XCTAssertTrue(choice.exists); choice.tap()
                XCTAssertTrue(app.staticTexts["Preview Review Twin Trail North"].waitForExistence(timeout: 10))
            }
            app.navigationBars.buttons.element(boundBy: 0).tap()
        }
    }


    func testLongNameAndEditionWarnings() async throws {
        continueAfterFailure = false
        let app = try await signIn(accessibilitySize: true)
        let longName = "Preview Review Alpine Traverse With an Extra Long Race Name Across the National Park"
        let row = app.staticTexts[longName]
        find(row, in: app); XCTAssertTrue(row.exists); row.tap()
        let unknown = app.staticTexts["Course edition not recorded"]
        find(unknown, in: app)
        XCTAssertTrue(unknown.waitForExistence(timeout: 10))
        try capture(app, "native-long-name-unknown-edition")
        app.navigationBars.buttons.element(boundBy: 0).tap()
        let older = app.staticTexts.matching(identifier: "Preview Review Mountain Trail").element(boundBy: 1)
        find(older, in: app); XCTAssertTrue(older.exists); older.tap()
        let warning = app.staticTexts["Course profile: 2026; your result: 2024"]
        find(warning, in: app)
        XCTAssertTrue(warning.waitForExistence(timeout: 10))
        try capture(app, "native-different-edition")
    }

    func testConfirmRoadResultsRefreshMeAndAddManualResult() async throws {
        continueAfterFailure = false
        let app = try await signIn()
        let confirm = app.buttons["This is my result"].firstMatch
        find(confirm, in: app)
        XCTAssertTrue(confirm.exists)
        try capture(app, "native-pending-vbm")
        confirm.tap()
        let remaining = app.buttons["This is my result"].firstMatch
        find(remaining, in: app)
        XCTAssertTrue(remaining.waitForExistence(timeout: 10))
        remaining.tap()
        let fm = app.staticTexts["race.pb.fm"]
        find(fm, in: app, up: false)
        XCTAssertEqual(fm.label, "3:39:14")
        XCTAssertEqual(app.staticTexts["race.pb.hm"].label, "1:44:04")
        app.navigationBars.buttons["Me"].tap()
        find(app.staticTexts["race.pb.fm"], in: app, up: false)
        XCTAssertEqual(app.staticTexts["race.pb.fm"].label, "3:39:14")
        try capture(app, "native-confirmed-me")
        let history = app.buttons["Race history"]
        find(history, in: app)
        history.tap()
        app.buttons["Add result"].tap()
        let name = app.textFields["race.form.name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap(); name.typeText("My manual half marathon")
        let distance = app.textFields["race.form.distance"]
        find(distance, in: app); distance.tap(); distance.typeText("21.0975")
        let time = app.textFields["race.form.time"]
        // The decimal pad is up and the lazy Form had scrolled past the time row; look back toward it.
        find(time, in: app, up: false)
        if !time.isHittable { find(time, in: app) }
        XCTAssertTrue(time.exists && time.isHittable, "Finish time must remain available for a finished result")
        time.tap(); time.typeText("1:50:00")
        try capture(app, "native-manual-form")
        app.buttons["race.form.save"].tap()
        let added = app.staticTexts["My manual half marathon"]
        XCTAssertTrue(added.waitForExistence(timeout: 10))
        // The name also appears in the achievement tile; the history row is the last match, further down the list.
        let rows = app.staticTexts.matching(identifier: "My manual half marathon")
        for _ in 0..<12 where !(rows.count > 1 && rows.element(boundBy: rows.count - 1).isHittable) { app.swipeUp() }
        rows.element(boundBy: rows.count - 1).tap()
        let edit = app.buttons["Edit result"]
        find(edit, in: app); edit.tap()
        let editingName = app.textFields["race.form.name"]
        XCTAssertTrue(editingName.waitForExistence(timeout: 5))
        editingName.tap()
        editingName.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: "My manual half marathon".count))
        editingName.typeText("My edited half marathon")
        try capture(app, "native-manual-edit")
        app.buttons["race.form.save"].tap()
        XCTAssertTrue(app.staticTexts["My edited half marathon"].waitForExistence(timeout: 10))
        let delete = app.buttons["Delete result"]
        find(delete, in: app); delete.tap()
        let confirms = app.buttons.matching(identifier: "Delete result")
        XCTAssertTrue(confirms.element(boundBy: 0).waitForExistence(timeout: 5))
        let tappable = confirms.allElementsBoundByIndex.filter { $0.isHittable }
        tappable.last?.tap()
        XCTAssertTrue(app.navigationBars["Race History"].waitForExistence(timeout: 10))
        let gone = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: app.staticTexts["My edited half marathon"])
        if await XCTWaiter().fulfillment(of: [gone], timeout: 10) != .completed { try capture(app, "debug-after-delete") }
        XCTAssertFalse(app.staticTexts["My edited half marathon"].exists)
    }
}
