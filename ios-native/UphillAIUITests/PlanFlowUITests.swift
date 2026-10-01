import XCTest

/// Runs against the LOCAL backend with the preview athlete seeded by
/// backend/scripts/seed_ios_preview.py. Use ios-native/scripts/e2e.sh.
final class PlanFlowUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    @MainActor
    func testSignInSeeTodayMarkDoneAndUndo() {
        let app = XCUIApplication()
        // `-KEY value` launch arguments land in UserDefaults' argument domain.
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local", "-UITEST_NO_AUTOFILL", "YES"]
        app.launch()

        let email = app.textFields["signin.email"]
        let today = app.descendants(matching: .any)["day.today"]
        // A previous test may have left a brand-new account signed in: its Welcome cover blocks the app.
        let notNow = app.buttons["Not now"]
        if notNow.waitForExistence(timeout: 5) { notNow.tap() }
        // Signed out, or signed in as whoever the last run left behind (maybe a plan-less new account).
        _ = email.waitForExistence(timeout: 10)

        // The Keychain session survives reinstalls on the simulator: sign out
        // first so the sign-in typing path runs every time.
        if !email.exists {
            app.tabBars.buttons["Me"].tap()
            let signOut = app.buttons["Sign out"]
            for _ in 0..<4 where !signOut.isHittable { app.swipeUp() }
            XCTAssertTrue(signOut.waitForExistence(timeout: 5))
            signOut.tap()
            XCTAssertTrue(email.waitForExistence(timeout: 10), "Sign out should return to sign-in")
        }

        email.tap()
        email.typeText("ios-preview@uphill.ai")
        let password = app.secureTextFields["signin.password"]
        password.tap()
        password.typeText("uphill-preview-1")
        app.buttons["signin.submit"].tap()

        // iOS offers to save the password after sign-in; it blocks taps until dismissed.
        dismissSavePrompt(app, wait: 10)

        XCTAssertTrue(today.waitForExistence(timeout: 30), "Plan should open scrolled to today")

        // Let the scroll-to-today animation settle so tap coordinates are stable.
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 2)

        // Today's workout if it has one; otherwise the first hittable workout row
        // anywhere in the list (the seeded Thursday is a rest day).
        let workoutPredicate = NSPredicate(format: "identifier BEGINSWITH 'workout.'")
        let workouts = app.buttons.matching(workoutPredicate)
        func firstHittable() -> XCUIElement? {
            let window = app.windows.firstMatch.frame
            // Visible below the nav bar and above the tab bar (isHittable is unreliable for these rows).
            return workouts.allElementsBoundByIndex.first {
                $0.exists && !$0.label.hasSuffix("done") && $0.frame.midY > window.minY + 130 && $0.frame.midY < window.maxY - 100
            }
        }
        _ = workouts.firstMatch.waitForExistence(timeout: 10)
        var found = firstHittable()
        for _ in 0..<6 where found == nil { app.swipeUp(); found = firstHittable() }
        for _ in 0..<12 where found == nil { app.swipeDown(); found = firstHittable() }
        guard let target = found else {
            XCTFail("No hittable workout row found anywhere in the plan")
            return
        }
        dismissSavePrompt(app, wait: 1)   // belt and braces; the launch flag should prevent it
        let targetLabel = target.label

        // Bring the row to the middle of the screen (clear of nav bar and tab bar), then tap its centre.
        let window = app.windows.firstMatch.frame
        if target.frame.midY < window.height * 0.3 || target.frame.midY > window.height * 0.65 {
            let from = target.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
            let to = app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.45))
            from.press(forDuration: 0.1, thenDragTo: to)
            _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1.5)
        }
        let sheetMarker = app.buttons["Done"]
        for attempt in 1...2 {
            let row = app.buttons[target.identifier]
            row.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
            if sheetMarker.waitForExistence(timeout: 6) { break }
            if attempt == 2 {
                let shot = XCTAttachment(screenshot: app.screenshot())
                shot.lifetime = .keepAlways
                add(shot)
                XCTFail("Detail sheet should open for \(targetLabel)")
                return
            }
        }

        let markDone = app.buttons["detail.markDone"]
        let undoDone = app.buttons["detail.undoDone"]
        // The sheet opens at a medium detent: the action buttons may sit below the fold.
        _ = markDone.waitForExistence(timeout: 5)
        for _ in 0..<4 where !markDone.exists && !undoDone.exists { app.swipeUp() }
        XCTAssertTrue(markDone.exists || undoDone.exists, "Workout sheet should offer Mark as done or Undo done")
        if undoDone.exists {
            undoDone.tap()   // seeded as done already: reset first
        }
        XCTAssertTrue(markDone.waitForExistence(timeout: 10))
        markDone.tap()
        XCTAssertTrue(undoDone.waitForExistence(timeout: 10))
        undoDone.tap()
        XCTAssertTrue(markDone.waitForExistence(timeout: 10))
    }

    /// iOS offers to save the password after sign-in; it blocks taps until dismissed.
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
