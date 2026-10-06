import XCTest

/// Fresh account → onboarding → generated plan, against the LOCAL backend.
/// Registers a new `ios-e2e-<timestamp>@uphill.ai` account on every run (local database only).
final class OnboardingFlowUITests: XCTestCase {
    override func setUp() { continueAfterFailure = false }

    @MainActor
    func testNewAthleteGetsAPlan() {
        let app = XCUIApplication()
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local", "-UITEST_NO_AUTOFILL", "YES"]
        app.launch()

        let emailField = app.textFields["signin.email"]
        let today = app.descendants(matching: .any)["day.today"]
        // A previous run may have left an account signed in; its Welcome cover blocks the app.
        let notNow = app.buttons["Not now"]
        if notNow.waitForExistence(timeout: 5) { notNow.tap() }
        _ = emailField.waitForExistence(timeout: 10)
        // The Keychain session survives reinstalls on the simulator: sign out first.
        if !emailField.exists {
            app.tabBars.buttons["Me"].tap()
            let signOut = app.buttons["Sign out"]
            for _ in 0..<4 where !signOut.isHittable { app.swipeUp() }
            signOut.tap()
            XCTAssertTrue(emailField.waitForExistence(timeout: 10))
        }

        app.buttons["New to Uphill? Create an account"].tap()
        let name = app.textFields["signin.name"]
        XCTAssertTrue(name.waitForExistence(timeout: 10))
        name.tap(); name.typeText("E2E Runner")
        emailField.tap(); emailField.typeText("ios-e2e-\(Int(Date().timeIntervalSince1970))@uphill.ai")
        let password = app.secureTextFields["signin.password"]
        password.tap(); password.typeText("uphill-e2e-pass-1")
        app.buttons["signin.submit"].tap()
        dismissSavePrompt(app)

        XCTAssertTrue(app.buttons["welcome.start"].waitForExistence(timeout: 20))
        app.buttons["welcome.start"].tap()
        let goal = app.descendants(matching: .any)["goal.start_running"].firstMatch
        XCTAssertTrue(goal.waitForExistence(timeout: 10))
        goal.tap()                                   // → schedule
        let primary = app.buttons["setup.primary"]
        XCTAssertTrue(primary.waitForExistence(timeout: 5))
        primary.tap()                                // schedule (defaults are valid) → about you
        primary.tap()                                // about you is optional → review
        XCTAssertEqual(primary.label, "Build my plan")
        primary.tap()

        let seePlan = app.buttons["generation.seePlan"]
        XCTAssertTrue(app.staticTexts["generation.running"].waitForExistence(timeout: 15) || seePlan.exists)
        XCTAssertTrue(seePlan.waitForExistence(timeout: 240), "Generation should finish")
        seePlan.tap()
        XCTAssertTrue(today.waitForExistence(timeout: 20) || app.staticTexts["Week 1"].waitForExistence(timeout: 5))
    }

    /// iOS offers to save the password after sign-up; it blocks taps until dismissed.
    private func dismissSavePrompt(_ app: XCUIApplication) {
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        for candidate in [app.buttons["Not Now"], springboard.buttons["Not Now"]] where candidate.waitForExistence(timeout: 5) {
            candidate.tap()
            return
        }
    }
}
