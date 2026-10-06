import Foundation
@testable import UphillAI

/// Loads JSON recorded by scripts/record_fixtures.sh straight from the source
/// tree (the simulator shares the Mac's file system), so fixtures need no
/// bundle resources.
enum Fixture {
    private static let directory = URL(filePath: #filePath)
        .deletingLastPathComponent()   // Support/
        .deletingLastPathComponent()   // UphillAITests/
        .appending(path: "Fixtures")

    static func data(_ name: String) throws -> Data {
        try Data(contentsOf: directory.appending(path: name))
    }

    static func decode<T: Decodable>(_ type: T.Type, _ name: String) throws -> T {
        try JSONCoding.decoder.decode(T.self, from: data(name))
    }
}
