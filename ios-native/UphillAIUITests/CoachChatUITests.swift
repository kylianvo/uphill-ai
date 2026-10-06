import XCTest

/// Runs against the LOCAL backend with the preview athlete seeded by
/// backend/scripts/seed_ios_preview.py. Use ios-native/scripts/e2e.sh.
final class CoachChatUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    @MainActor
    func testCoachChatFlow() {
        let app = XCUIApplication()
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local", "-UITEST_NO_AUTOFILL", "YES"]
        app.launch()

        let email = app.textFields["signin.email"]
        let notNow = app.buttons["Not now"]
        if notNow.waitForExistence(timeout: 5) { notNow.tap() }

        _ = email.waitForExistence(timeout: 10)

        // Ensure we are signed in
        if !email.exists {
            let coachTab = app.tabBars.buttons["Coach"]
            if !coachTab.exists {
                app.tabBars.buttons["Me"].tap()
                let signOut = app.buttons["Sign out"]
                for _ in 0..<4 where !signOut.isHittable { app.swipeUp() }
                XCTAssertTrue(signOut.waitForExistence(timeout: 5))
                signOut.tap()
                XCTAssertTrue(email.waitForExistence(timeout: 10))
            }
        }

        if email.exists {
            email.tap()
            email.typeText("ios-preview@uphill.ai")
            let password = app.secureTextFields["signin.password"]
            password.tap()
            password.typeText("uphill-preview-1")
            app.buttons["signin.submit"].tap()

            dismissSavePrompt(app, wait: 10)
        }

        // Tap Coach tab
        let coachTab = app.tabBars.buttons["Coach"]
        XCTAssertTrue(coachTab.waitForExistence(timeout: 20), "Coach tab must exist")
        coachTab.tap()

        // Settle UI
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1)

        // Verify Coach navigation title and input field exist
        let inputField = app.textFields["chat.inputField"]
        XCTAssertTrue(inputField.waitForExistence(timeout: 10), "Chat input field should be visible")

        // Check send button initially exists and disabled when input is empty
        let sendButton = app.buttons["chat.sendButton"]
        XCTAssertTrue(sendButton.exists, "Send button should exist")
        XCTAssertFalse(sendButton.isEnabled, "Send button should be disabled for empty text")

        // Tap a starter chip or send a message
        let starterChip = app.buttons["chat.starterChip"].firstMatch
        if starterChip.waitForExistence(timeout: 5) {
            starterChip.tap()
        } else {
            inputField.tap()
            inputField.typeText("Explain Zone 2 training")
            sendButton.tap()
        }

        // Expect streaming response to arrive (assistant message appears)
        let assistantHeader = app.staticTexts["Coach Uphill"].firstMatch
        XCTAssertTrue(assistantHeader.waitForExistence(timeout: 35), "Assistant response should appear")

        // Wait for streaming to finish (input field becomes enabled again)
        let isIdlePredicate = NSPredicate(format: "isEnabled == true")
        let idleExpectation = XCTNSPredicateExpectation(predicate: isIdlePredicate, object: inputField)
        _ = XCTWaiter.wait(for: [idleExpectation], timeout: 35)

        // If feedback buttons exist, tap thumbs up
        let thumbsUp = app.buttons["chat.thumbsUp"].firstMatch
        if thumbsUp.waitForExistence(timeout: 5) {
            thumbsUp.tap()
        }

        // If sources button exists, open and dismiss it
        let sourcesButton = app.buttons["chat.sourcesButton"].firstMatch
        if sourcesButton.waitForExistence(timeout: 5) {
            sourcesButton.tap()
            let doneButton = app.buttons["chat.sourcesDone"]
            XCTAssertTrue(doneButton.waitForExistence(timeout: 5), "Sources sheet Done button should exist")
            doneButton.tap()
        }
    }

    @MainActor
    private func dismissSavePrompt(_ app: XCUIApplication, wait: TimeInterval) {
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        let predicate = NSPredicate(format: "label == 'Not Now' OR identifier == 'Not Now'")
        for host in [app, springboard] {
            let notNow = host.descendants(matching: .any).matching(predicate).firstMatch
            if notNow.waitForExistence(timeout: wait) { notNow.tap(); return }
        }
    }
}
