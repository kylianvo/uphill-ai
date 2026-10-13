import XCTest

/// Fresh account → onboarding → generated plan, against the LOCAL backend.
/// Registers a new `ios-e2e-<timestamp>@uphill.ai` account on every run (local database only).
final class OnboardingFlowUITests: XCTestCase {
    override func setUp() { continueAfterFailure = false }

    @MainActor
    func testNewAthleteGetsAPlan() {
        let app = XCUIApplication()
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local", "-UITEST_NO_AUTOFILL", "YES", "-appLanguage", "en"]
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
        app.buttons["signin.keyboardDone"].tap()
        let password = app.secureTextFields["signin.password"]
        password.tap(); password.typeText("uphill-e2e-pass-1")
        app.buttons["signin.keyboardDone"].tap()
        app.buttons["signin.submit"].tap()
        dismissSavePrompt(app, wait: 10)

        let welcomeStart = app.buttons["welcome.start"]
        XCTAssertTrue(welcomeStart.waitForExistence(timeout: 20))

        let saveSheet = app.sheets["Save Password?"]
        if saveSheet.waitForExistence(timeout: 4) {
            saveSheet.buttons["Not Now"].tap()
        }

        if !welcomeStart.isHittable && saveSheet.exists {
            saveSheet.buttons["Not Now"].tap()
        }

        XCTAssertTrue(welcomeStart.waitForExistence(timeout: 5))
        welcomeStart.tap()

        let goal = app.descendants(matching: .any)["goal.start_running"].firstMatch
        XCTAssertTrue(goal.waitForExistence(timeout: 15))
        XCTAssertFalse(app.buttons["goal.return"].exists)
        XCTAssertFalse(app.buttons["goal.recovery"].exists)
        goal.tap()                                   // → schedule
        let primary = app.buttons["setup.primary"]
        XCTAssertTrue(primary.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["What does your week look like?"].exists)
        app.buttons["setup.noRunning"].tap()
        primary.tap()                                // schedule → venues
        XCTAssertTrue(app.staticTexts["Where do you train?"].waitForExistence(timeout: 5))
        primary.tap()                                // venues → body
        XCTAssertTrue(app.staticTexts["How does your body hold up?"].waitForExistence(timeout: 5))
        primary.tap()                                // body → training zones
        XCTAssertTrue(app.staticTexts["Set your training zones"].waitForExistence(timeout: 5))
        app.buttons["setup.zonesGuide"].tap()
        XCTAssertTrue(app.navigationBars["Training zones guide"].waitForExistence(timeout: 5))
        app.segmentedControls.buttons["Field test"].tap()
        XCTAssertTrue(app.staticTexts["Aerobic Threshold (AeT)"].exists)
        app.buttons["Got it"].tap()
        XCTAssertEqual(primary.label, "Skip for now")
        primary.tap()                                // unknown zones → warning
        XCTAssertTrue(app.alerts["Continue with estimated zones?"].waitForExistence(timeout: 5))
        let warningCapture = XCTAttachment(screenshot: app.screenshot())
        warningCapture.name = "onboarding-zone-estimate-warning"
        warningCapture.lifetime = .keepAlways
        add(warningCapture)
        app.alerts.buttons["Continue with estimates"].tap()
        XCTAssertTrue(app.staticTexts["Have you raced before?"].waitForExistence(timeout: 5))
        XCTAssertEqual(primary.label, "Skip for now")
        primary.tap()                                // race history → start date
        XCTAssertTrue(app.staticTexts["When do you want to start?"].waitForExistence(timeout: 5))
        primary.tap()                                // start date → review
        XCTAssertTrue(app.staticTexts["Here's what I'll build from"].waitForExistence(timeout: 5))
        XCTAssertEqual(primary.label, "Build my plan")
        primary.tap()

        let seePlan = app.buttons["generation.seePlan"]
        XCTAssertTrue(app.staticTexts["generation.running"].waitForExistence(timeout: 15) || seePlan.exists)
        XCTAssertTrue(seePlan.waitForExistence(timeout: 240), "Generation should finish")
        seePlan.tap()
        XCTAssertTrue(today.waitForExistence(timeout: 20) || app.staticTexts["Week 1"].waitForExistence(timeout: 5))
    }

    /// iOS offers to save the password after sign-up; it blocks taps until dismissed.
    @MainActor
    private func dismissSavePrompt(_ app: XCUIApplication, wait: TimeInterval = 10) {
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        let predicate = NSPredicate(format: "label == 'Not Now' OR identifier == 'Not Now'")
        for host in [app, springboard] {
            let notNow = host.descendants(matching: .any).matching(predicate).firstMatch
            if notNow.waitForExistence(timeout: wait) { notNow.tap(); return }
        }
    }
}
