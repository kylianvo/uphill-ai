import Foundation

struct OnboardingBody: Encodable, Sendable { var skipPlan = false }
struct PlanBody: Encodable, Sendable { var goalType = "" }
