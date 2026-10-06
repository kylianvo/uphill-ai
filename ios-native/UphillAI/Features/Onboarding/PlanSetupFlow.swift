import SwiftUI

struct PlanSetupFlow: View {
    @Bindable var model: PlanSetupViewModel
    let onClose: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var transition: AnyTransition {
        if reduceMotion { return .opacity }
        return .asymmetric(
            insertion: .move(edge: model.direction == .forward ? .trailing : .leading).combined(with: .opacity),
            removal: .move(edge: model.direction == .forward ? .leading : .trailing).combined(with: .opacity))
    }

    var body: some View {
        VStack(spacing: UH.Space.regular) {
            HStack {
                Button { model.back() } label: { Image(systemName: "chevron.left").frame(width: 44, height: 44) }
                    .accessibilityLabel("Back").opacity(model.isFirstStep ? 0 : 1).disabled(model.isFirstStep)
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        Capsule().fill(UH.Palette.line)
                        Capsule().fill(UH.Palette.accent).frame(width: geometry.size.width * model.progress)
                    }
                }.frame(height: 4).accessibilityLabel("Setup progress").accessibilityValue("Step \(model.stepIndex + 1) of \(model.steps.count)")
                Button(action: onClose) { Image(systemName: "xmark").frame(width: 44, height: 44) }.accessibilityLabel("Close")
            }
            .padding(.horizontal, UH.Space.small)
            ScrollViewReader { proxy in
                ScrollView {
                    SetupSteps(model: model)
                        .padding(UH.Space.section)
                        .id(model.step)
                        .transition(transition)
                }
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: model.issues) { _, issues in
                    if let field = issues.first?.field { proxy.scrollTo(field, anchor: .center) }
                }
                .onChange(of: model.step) { _, step in proxy.scrollTo(step, anchor: .top) }
            }
        }
        .safeAreaInset(edge: .bottom) {
            if model.step != .goal {
                VStack(spacing: UH.Space.small) {
                    if let error = model.submitError { Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
                    Button {
                        if model.isLastStep { Task { await model.submit() } } else { model.next() }
                    } label: {
                        if model.isSubmitting { ProgressView() } else { Text(model.primaryTitle) }
                    }.buttonStyle(.uhPrimary).disabled(model.isSubmitting).accessibilityIdentifier("setup.primary")
                    if model.mode == .onboarding && model.isLastStep {
                        Button("Save my profile, build a plan later") { Task { await model.saveProfileOnly() } }
                            .font(UH.TextStyle.caption).frame(minHeight: 44).disabled(model.isSubmitting)
                    }
                }.padding(UH.Space.regular).background(UH.Palette.surface)
            }
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .foregroundStyle(UH.Palette.ink)
        .tint(UH.Palette.accentInk)
        .animation(reduceMotion ? .easeInOut(duration: 0.15) : UH.Motion.standard, value: model.stepIndex)
        .sensoryFeedback(.selection, trigger: model.stepIndex)
        .onChange(of: model.didStart) { _, started in if started { onClose() } }
    }
}
