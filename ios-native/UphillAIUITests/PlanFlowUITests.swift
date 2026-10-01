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
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local"]
        app.launch()

        let email = app.textFields["signin.email"]
        let today = app.descendants(matching: .any)["day.today"]
        // The session lives in the Keychain, which survives reinstalls on the
        // simulator, so the app may open straight on the plan.
        XCTAssertTrue(email.waitForExistence(timeout: 10) || today.exists, "Expected sign-in or the plan")
        if email.exists {
            email.tap()
            email.typeText("ios-preview@uphill.ai")
            let password = app.secureTextFields["signin.password"]
            password.tap()
            password.typeText("uphill-preview-1")
            app.buttons["signin.submit"].tap()
        }

        XCTAssertTrue(today.waitForExistence(timeout: 15), "Plan should open scrolled to today")

        let firstWorkout = today.buttons.matching(NSPredicate(format: "identifier BEGINSWITH 'workout.'")).firstMatch
        guard firstWorkout.exists else {
            // Today is a rest day in the seeded week: nothing to mark.
            return
        }
        firstWorkout.tap()

        let markDone = app.buttons["detail.markDone"]
        let undoDone = app.buttons["detail.undoDone"]
        if undoDone.waitForExistence(timeout: 3) {
            undoDone.tap()   // seeded as done already: reset first
        }
        XCTAssertTrue(markDone.waitForExistence(timeout: 5))
        markDone.tap()
        XCTAssertTrue(undoDone.waitForExistence(timeout: 10))
        undoDone.tap()
        XCTAssertTrue(markDone.waitForExistence(timeout: 10))
    }
}
