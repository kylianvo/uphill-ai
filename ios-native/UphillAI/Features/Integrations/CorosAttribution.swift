import SwiftUI

/// Attribution for COROS-sourced data.
///
/// Required by COROS API Agreement clause 14.5: wherever COROS data or data derived
/// from it is displayed, we must show an attribution naming COROS AND the
/// specific device model, no less prominent than any other source. Failure is
/// defined as a material breach, so this is not a decorative component.
public struct CorosAttribution: View {
    public let deviceModel: String?
    public let provider: String

    public init(deviceModel: String? = nil, provider: String = "coros") {
        self.deviceModel = deviceModel
        self.provider = provider
    }

    public var body: some View {
        if provider == "coros" {
            HStack(spacing: 5) {
                if UIImage(named: "coros_mark") != nil {
                    Image("coros_mark")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 12, height: 12)
                }
                Text(attributionText)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(UH.Palette.secondary)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(attributionText)
        }
    }

    private var attributionText: String {
        if let deviceModel, !deviceModel.isEmpty {
            return L("Data provided by COROS · %@", deviceModel)
        }
        return L("Data provided by COROS")
    }
}
