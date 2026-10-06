import SwiftUI

struct CoachNoteThreadView: View {
    let athleteId: Int
    let targetType: String // "workout", "week", "plan"
    let targetId: Int?
    let service: any CoachingServicing
    var canAdd: Bool = true
    var audience: CoachNoteThreadPresentation.Audience = .coach

    @State private var notes: [CoachNote] = []
    @State private var draft = ""
    @State private var isLoading = false
    @State private var isSubmitting = false
    @State private var isExpanded = true
    @State private var errorMessage: String? = nil

    private var presentation: CoachNoteThreadPresentation {
        CoachNoteThreadPresentation(audience: audience, athleteId: athleteId, targetType: targetType, notes: notes)
    }

    var body: some View {
        // The task lives outside the conditional so an athlete's hidden thread still loads.
        Group {
            if presentation.isVisible { thread }
        }
        .task {
            await loadNotes()
        }
    }

    private var thread: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Button {
                withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "bubble.left.and.bubble.right.fill")
                        .font(.system(size: 13))
                        .foregroundStyle(UH.Palette.accent)
                    Text(presentation.title)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(.vertical, 4)
            }
            .buttonStyle(.plain)

            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    if isLoading && notes.isEmpty {
                        ProgressView()
                            .padding(.vertical, 8)
                    } else if notes.isEmpty {
                        Text(presentation.emptyText)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.muted)
                            .padding(.vertical, 4)
                    } else {
                        VStack(spacing: 6) {
                            ForEach(notes) { note in
                                VStack(alignment: .leading, spacing: 2) {
                                    if let author = presentation.authorLabel(for: note) {
                                        Text(author.uppercased())
                                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                                            .foregroundStyle(UH.Palette.muted)
                                    }
                                    Text(note.note)
                                        .font(UH.TextStyle.body)
                                        .foregroundStyle(UH.Palette.ink)
                                    if let date = note.createdAt {
                                        Text(date)
                                            .font(.system(size: 10, design: .monospaced))
                                            .foregroundStyle(UH.Palette.muted)
                                    }
                                }
                                .padding(10)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(UH.Palette.hover.opacity(0.6))
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            }
                        }
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(Color.red)
                    }

                    if canAdd {
                        HStack(spacing: 8) {
                            TextField(presentation.placeholder, text: $draft)
                                .font(UH.TextStyle.body)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 8)
                                .background(UH.Palette.hover)
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(
                                    RoundedRectangle(cornerRadius: UH.Radius.control)
                                        .stroke(UH.Palette.line, lineWidth: 1)
                                )

                            Button {
                                Task { await postNote() }
                            } label: {
                                if isSubmitting {
                                    ProgressView()
                                        .frame(width: 44, height: 32)
                                } else {
                                    Text(presentation.postLabel)
                                        .font(UH.TextStyle.label)
                                        .padding(.horizontal, 14)
                                        .padding(.vertical, 8)
                                }
                            }
                            .buttonStyle(.uhPrimary)
                            .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSubmitting)
                        }
                        .padding(.top, 4)
                    }
                }
            }
        }
        .trainingCard()
    }

    private func loadNotes() async {
        isLoading = true
        errorMessage = nil
        do {
            notes = try await service.fetchNotes(athleteId: athleteId, targetType: targetType, targetId: targetId)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func postNote() async {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        isSubmitting = true
        errorMessage = nil
        do {
            let payload = CoachNoteCreatePayload(targetType: targetType, targetId: targetId, note: text)
            let created = try await service.addNote(athleteId: athleteId, payload: payload)
            notes.insert(created, at: 0)
            draft = ""
        } catch {
            errorMessage = error.localizedDescription
        }
        isSubmitting = false
    }
}
