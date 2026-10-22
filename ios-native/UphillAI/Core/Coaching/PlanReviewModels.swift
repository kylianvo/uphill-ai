import Foundation

/// GET/POST /api/coaching/athletes/{id}/plans/{plan_id}/review: weeks generated vs reviewed, plan-check findings, goal fit.
struct PlanReview: Codable, Sendable, Equatable {
    let generatedBlock: Int
    let reviewedBlock: Int?
    let reviewedAt: String?
    let reviewedBy: Int?
    let issues: [PlanReviewIssue]
    let feasibility: String?
    let levers: [String]

    var needsReview: Bool { generatedBlock > (reviewedBlock ?? 0) }
}

struct PlanReviewIssue: Codable, Sendable, Equatable {
    let code: String
    let week: Int
    let message: String
}

/// POST .../publish: every pending session approved, a draft made active.
struct PublishResult: Codable, Sendable, Equatable {
    let planId: Int
    let planStatus: String
    let approvedCount: Int
}

/// One plain sentence per plan-check code. The server's `message` is written for the model's retry prompt,
/// so it's only shown for a code this build doesn't know yet.
enum PlanReviewText {
    static let codes = [
        "BACK_TO_BACK", "CLIMB_SPECIFICITY", "DAYS_SHORT", "HARD_ADJACENT", "HARD_IN_DOWN_WEEK", "LONG_RUN_DAY",
        "LONG_RUN_GRADIENT", "LONG_RUN_JUMP", "LONG_SHARE", "ME_LOAD", "ME_SPACING", "QUALITY_COUNT", "RECOVERY_DUE",
        "SESSION_TOO_LONG", "SPECIFICITY_LATE", "TAPER_NOT_LIGHT", "TIME_ON_FEET", "ULTRA_LADDER", "VERT_JUMP",
        "VOLUME_JUMP", "WEEKDAY_SHORT",
    ]

    private static let english: [String: String] = [
        "BACK_TO_BACK": "Week %lld: back-to-back long days need a check",
        "CLIMB_SPECIFICITY": "Week %lld: too little climbing for the race",
        "DAYS_SHORT": "Week %lld: fewer run days than the runner set",
        "HARD_ADJACENT": "Week %lld: two hard days in a row",
        "HARD_IN_DOWN_WEEK": "Week %lld: hard session in a recovery week",
        "LONG_RUN_DAY": "Week %lld: Long Run not on the chosen day",
        "LONG_RUN_GRADIENT": "Week %lld: Long Run is flatter than the race",
        "LONG_RUN_JUMP": "Week %lld: Long Run grows too fast",
        "LONG_SHARE": "Week %lld: Long Run is too big a share of the week",
        "ME_LOAD": "Week %lld: too much Muscular Endurance",
        "ME_SPACING": "Week %lld: Muscular Endurance sessions too close",
        "QUALITY_COUNT": "Week %lld: too many quality sessions",
        "RECOVERY_DUE": "Week %lld: a recovery week is due",
        "SESSION_TOO_LONG": "Week %lld: a session is too long for this runner",
        "SPECIFICITY_LATE": "Week %lld: race-specific work starts too late",
        "TAPER_NOT_LIGHT": "Week %lld: Taper isn't light enough",
        "TIME_ON_FEET": "Week %lld: not enough time on feet for the race",
        "ULTRA_LADDER": "Week %lld: Long Run skips a step of the ultra ladder",
        "VERT_JUMP": "Week %lld: climbing jumps too fast",
        "VOLUME_JUMP": "Week %lld: volume jumps too fast",
        "WEEKDAY_SHORT": "Week %lld: weekday runs are too short",
    ]

    static func sentence(_ issue: PlanReviewIssue, lang: AppLanguage = .current) -> String {
        guard let key = english[issue.code] else { return issue.message }
        return L(key, in: lang, issue.week)
    }
}

/// What the coach card offers, from the runner's signals and the plan the coach is looking at.
enum CoachFocus {
    static func primary(_ athlete: CoachOverviewAthlete?, planStatus: String?) -> CoachAction? {
        if planStatus == "draft" { return .openDraft }
        return athlete?.primaryAction
    }

    static func label(_ action: CoachAction) -> String {
        switch action {
        case .adaptWeek: L("Adapt this week")
        case .reviewPlan: L("Mark reviewed")
        case .buildPlan: L("Build plan")
        case .openDraft: L("Publish plan")
        case .buildNextWeek: L("Build next week")
        case .reviewChanges: L("Approve changes")
        case .note: L("Note")
        }
    }
}
