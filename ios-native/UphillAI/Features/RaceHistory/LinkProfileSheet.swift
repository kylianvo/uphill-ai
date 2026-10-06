import SwiftUI

struct LinkProfileSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any RaceHistoryServicing
    var onLinked: (() -> Void)? = nil

    @State private var source: String = "utmb"
    @State private var query: String = ""
    @State private var candidates: [RaceCandidate] = []
    @State private var isSearching: Bool = false
    @State private var isLinking: Bool = false
    @State private var errorMessage: String? = nil
    @State private var searched: Bool = false

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                // Info header
                VStack(alignment: .leading, spacing: 4) {
                    Text("IMPORT YOUR OFFICIAL RESULTS")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Text("Link your UTMB or Vietnam Backyards / VBM runner profile to automatically import past races.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                // Source picker
                Picker("Source", selection: $source) {
                    Text("UTMB Index").tag("utmb")
                    Text("Vietnam Trail / VBM").tag("vbm")
                }
                .pickerStyle(.segmented)

                // Search box
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(UH.Palette.muted)
                    TextField("Enter runner full name (as on bib)", text: $query)
                        .font(UH.TextStyle.body)
                        .submitLabel(.search)
                        .onSubmit {
                            Task { await search() }
                        }
                    if !query.isEmpty {
                        Button {
                            query = ""
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(UH.Palette.muted)
                        }
                    }
                }
                .padding(10)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                Button {
                    Task { await search() }
                } label: {
                    HStack {
                        if isSearching {
                            ProgressView().tint(Color.white)
                        } else {
                            Text("Search Athletes")
                        }
                    }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(Color.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(UH.Palette.ink, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }
                .disabled(isSearching || query.trimmingCharacters(in: .whitespaces).isEmpty)

                if let error = errorMessage {
                    Text(error)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.danger)
                        .padding(.vertical, 4)
                }

                Divider()

                // Candidates list
                if candidates.isEmpty && searched && !isSearching {
                    VStack(spacing: 6) {
                        Image(systemName: "person.slash")
                            .font(.system(size: 24))
                            .foregroundStyle(UH.Palette.muted)
                        Text("No athlete profiles found")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Text("Try searching with the exact spelling used during race registration.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, UH.Space.section)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(candidates) { candidate in
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(candidate.displayName)
                                            .font(UH.TextStyle.body.weight(.semibold))
                                            .foregroundStyle(UH.Palette.ink)
                                        HStack(spacing: 6) {
                                            if let age = candidate.ageGroup, !age.isEmpty {
                                                Text(age)
                                                    .font(UH.TextStyle.caption)
                                                    .foregroundStyle(UH.Palette.secondary)
                                            }
                                            if let index = candidate.index, index > 0 {
                                                Text("UTMB Index: \(Int(index))")
                                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                                    .foregroundStyle(UH.Palette.accentInk)
                                            }
                                        }
                                    }

                                    Spacer()

                                    Button {
                                        Task { await link(candidate) }
                                    } label: {
                                        Text("Link Profile")
                                            .font(UH.TextStyle.caption.weight(.bold))
                                            .foregroundStyle(UH.Palette.ink)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(UH.Palette.activeFill, in: Capsule())
                                            .overlay(Capsule().stroke(UH.Palette.accentInk, lineWidth: 1))
                                    }
                                    .disabled(isLinking)
                                }
                                .trainingCard()
                            }
                        }
                    }
                }
            }
            .padding(UH.Space.regular)
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Link Runner Profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }

    private func search() async {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isSearching = true
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .light).impactOccurred()

        do {
            candidates = try await service.searchCandidates(source: source, query: query.trimmingCharacters(in: .whitespaces))
            searched = true
        } catch {
            errorMessage = error.localizedDescription
        }
        isSearching = false
    }

    private func link(_ candidate: RaceCandidate) async {
        isLinking = true
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        do {
            try await service.addClaim(source: source, externalId: candidate.externalId)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            onLinked?()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
        isLinking = false
    }
}
