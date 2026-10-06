import XCTest

/// Tests opening all four tools (Goal Determiner, Gear Vault, Nutrition Lab, Shoe Rotation)
/// from Me tab and from Plan -> Manage without crashing.
final class ToolNavigationUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    @MainActor
    func testOpenAllToolsFromMeAndManageWithoutCrashing() {
        let app = XCUIApplication()
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local", "-UITEST_NO_AUTOFILL", "YES"]
        app.launch()

        signInIfNeeded(app)

        let planTab = app.tabBars.buttons["Plan"]
        let meTab = app.tabBars.buttons["Me"]

        // 1. Test opening tools from Me tab
        XCTAssertTrue(meTab.waitForExistence(timeout: 10), "Me tab should exist")
        meTab.tap()
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1.5)

        // 1a. Goal Determiner from Me
        let meGoal = app.buttons["me.tool.goalDeterminer"]
        for _ in 0..<4 where !meGoal.isHittable { app.swipeUp() }
        XCTAssertTrue(meGoal.waitForExistence(timeout: 5), "Goal Determiner button should exist on Me")
        meGoal.tap()
        let goalNavBar = app.navigationBars["Goal Determiner"]
        XCTAssertTrue(goalNavBar.waitForExistence(timeout: 10), "Goal Determiner should open from Me without crashing")
        popNavigation(app)

        // 1b. Nutrition Lab from Me
        let meNutrition = app.buttons["me.tool.nutritionLab"]
        for _ in 0..<4 where !meNutrition.isHittable { app.swipeUp() }
        XCTAssertTrue(meNutrition.waitForExistence(timeout: 5), "Nutrition Lab button should exist on Me")
        meNutrition.tap()
        let nutritionNavBar = app.navigationBars["Nutrition Lab"]
        XCTAssertTrue(nutritionNavBar.waitForExistence(timeout: 10), "Nutrition Lab should open from Me without crashing")
        popNavigation(app)

        // 1c. Gear Vault from Me
        let meGear = app.buttons["me.tool.gearVault"]
        for _ in 0..<4 where !meGear.isHittable { app.swipeUp() }
        XCTAssertTrue(meGear.waitForExistence(timeout: 5), "Gear Vault button should exist on Me")
        meGear.tap()
        let gearVaultNavBar = app.navigationBars["Gear Vault"]
        XCTAssertTrue(gearVaultNavBar.waitForExistence(timeout: 10), "Gear Vault should open from Me without crashing")
        popNavigation(app)

        // 1d. Shoe Rotation slot from Me (tapping slot opens Gear Vault)
        // Scroll back up to shoe rotation
        for _ in 0..<4 { app.swipeDown() }
        let shoeSlot = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH 'me.shoeRotation.'")).firstMatch
        if shoeSlot.waitForExistence(timeout: 5) && shoeSlot.isHittable {
            shoeSlot.tap()
            XCTAssertTrue(gearVaultNavBar.waitForExistence(timeout: 10), "Tapping shoe slot should open Gear Vault without crashing")
            popNavigation(app)
        }

        // 2. Test opening tools from Plan -> Manage
        XCTAssertTrue(planTab.waitForExistence(timeout: 10), "Plan tab should exist")
        planTab.tap()
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1.5)

        // 2a. Goal Determiner from Manage
        openManageTool(app, toolId: "manage.tool.goalDeterminer")
        XCTAssertTrue(goalNavBar.waitForExistence(timeout: 10), "Goal Determiner should open from Manage without crashing")
        popNavigation(app)

        // 2b. Gear Vault from Manage
        planTab.tap()
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1)
        openManageTool(app, toolId: "manage.tool.gearVault")
        XCTAssertTrue(gearVaultNavBar.waitForExistence(timeout: 10), "Gear Vault should open from Manage without crashing")
        popNavigation(app)

        // 2c. Nutrition Lab from Manage
        planTab.tap()
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1)
        openManageTool(app, toolId: "manage.tool.nutritionLab")
        XCTAssertTrue(nutritionNavBar.waitForExistence(timeout: 10), "Nutrition Lab should open from Manage without crashing")
        popNavigation(app)

        // 2d. Shoe Rotation from Manage
        planTab.tap()
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1)
        openManageTool(app, toolId: "manage.tool.shoeRotation")
        XCTAssertTrue(gearVaultNavBar.waitForExistence(timeout: 10), "Shoe Rotation should open from Manage without crashing")
        popNavigation(app)
    }

    @MainActor
    private func openManageTool(_ app: XCUIApplication, toolId: String) {
        let manageButton = app.buttons["plan.manageButton"]
        XCTAssertTrue(manageButton.waitForExistence(timeout: 10), "Manage button should exist on Plan tab")
        manageButton.tap()

        let toolRow = app.buttons[toolId]
        for _ in 0..<6 where !toolRow.isHittable {
            app.swipeUp()
        }
        XCTAssertTrue(toolRow.waitForExistence(timeout: 5), "Tool \(toolId) should exist in Manage")
        toolRow.tap()
    }

    @MainActor
    private func popNavigation(_ app: XCUIApplication) {
        let backButton = app.navigationBars.buttons.element(boundBy: 0)
        if backButton.waitForExistence(timeout: 5) && backButton.isHittable {
            backButton.tap()
        }
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 1)
    }

    @MainActor
    private func signInIfNeeded(_ app: XCUIApplication) {
        let email = app.textFields["signin.email"]
        let today = app.descendants(matching: .any)["day.today"]
        let notNow = app.buttons["Not now"]
        if notNow.waitForExistence(timeout: 5) { notNow.tap() }

        _ = email.waitForExistence(timeout: 5)
        if !email.exists && !today.exists {
            // Check if signed out or need to tap tab
            let planTab = app.tabBars.buttons["Plan"]
            if planTab.exists { planTab.tap() }
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

        XCTAssertTrue(today.waitForExistence(timeout: 30), "Plan should load and display today")
        _ = XCTWaiter.wait(for: [expectation(description: "settle")], timeout: 2)
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
