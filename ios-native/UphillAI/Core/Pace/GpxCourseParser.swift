import Foundation

struct GpxCourseResult: Sendable, Equatable {
    let fileName: String
    let totalDistanceKm: Double
    let totalElevationGainM: Double
    let totalElevationLossM: Double
    let minElevationM: Double
    let maxElevationM: Double
    let checkpoints: [CourseCheckpoint]
    let trackpointCount: Int
    let waypointNames: [String]

    init(
        fileName: String,
        totalDistanceKm: Double,
        totalElevationGainM: Double,
        totalElevationLossM: Double,
        minElevationM: Double,
        maxElevationM: Double,
        checkpoints: [CourseCheckpoint],
        trackpointCount: Int,
        waypointNames: [String]
    ) {
        self.fileName = fileName
        self.totalDistanceKm = totalDistanceKm
        self.totalElevationGainM = totalElevationGainM
        self.totalElevationLossM = totalElevationLossM
        self.minElevationM = minElevationM
        self.maxElevationM = maxElevationM
        self.checkpoints = checkpoints
        self.trackpointCount = trackpointCount
        self.waypointNames = waypointNames
    }
}

enum GpxParseError: LocalizedError, Sendable {
    case emptyData
    case invalidXml(String)
    case noTrackpointsFound
    case insufficientDistance

    var errorDescription: String? {
        switch self {
        case .emptyData:
            return "GPX file contains no data."
        case .invalidXml(let msg):
            return "Failed to parse GPX XML: \(msg)"
        case .noTrackpointsFound:
            return "No valid trackpoints (<trkpt>) found in the GPX file."
        case .insufficientDistance:
            return "Route distance is too short to generate course checkpoints."
        }
    }
}

/// Native GPX XML parser for trail and ultra routes.
final class GpxCourseParser: NSObject, XMLParserDelegate, @unchecked Sendable {

    private struct RawPoint {
        let lat: Double
        let lon: Double
        let ele: Double?
    }

    private struct RawWaypoint {
        let name: String
        let lat: Double
        let lon: Double
        let ele: Double?
    }

    private var rawPoints: [RawPoint] = []
    private var rawWaypoints: [RawWaypoint] = []

    private var currentElement: String = ""
    private var currentText: String = ""
    private var currentLat: Double?
    private var currentLon: Double?
    private var currentEle: Double?
    private var currentWptName: String?
    private var isInPoint: Bool = false
    private var isInWaypoint: Bool = false

    static func parse(data: Data, fileName: String, intervalKm: Double = 5.0) throws -> GpxCourseResult {
        guard !data.isEmpty else {
            throw GpxParseError.emptyData
        }

        let parserDelegate = GpxCourseParser()
        let xmlParser = XMLParser(data: data)
        xmlParser.delegate = parserDelegate
        xmlParser.shouldProcessNamespaces = false
        xmlParser.shouldReportNamespacePrefixes = false
        xmlParser.shouldResolveExternalEntities = false

        let success = xmlParser.parse()
        if !success, let parserError = xmlParser.parserError {
            // If XMLParser failed on strict syntax, try extracting points via regex fallback
            if let fallbackResult = parserDelegate.parseViaRegexFallback(data: data, fileName: fileName, intervalKm: intervalKm) {
                return fallbackResult
            }
            throw GpxParseError.invalidXml(parserError.localizedDescription)
        }

        return try parserDelegate.buildResult(fileName: fileName, intervalKm: intervalKm)
    }

    // MARK: - XMLParserDelegate

    func parser(
        _ parser: XMLParser,
        didStartElement elementName: String,
        namespaceURI: String?,
        qualifiedName qName: String?,
        attributes attributeDict: [String : String] = [:]
    ) {
        currentElement = elementName.lowercased()
        currentText = ""

        if currentElement == "trkpt" || currentElement == "rtept" {
            isInPoint = true
            currentLat = Double(attributeDict["lat"] ?? "")
            currentLon = Double(attributeDict["lon"] ?? "")
            currentEle = nil
        } else if currentElement == "wpt" {
            isInWaypoint = true
            currentLat = Double(attributeDict["lat"] ?? "")
            currentLon = Double(attributeDict["lon"] ?? "")
            currentEle = nil
            currentWptName = nil
        }
    }

    func parser(_ parser: XMLParser, foundCharacters string: String) {
        currentText += string
    }

    func parser(
        _ parser: XMLParser,
        didEndElement elementName: String,
        namespaceURI: String?,
        qualifiedName qName: String?
    ) {
        let tag = elementName.lowercased()
        let trimmed = currentText.trimmingCharacters(in: .whitespacesAndNewlines)

        if tag == "ele" {
            currentEle = Double(trimmed)
        } else if tag == "name" && isInWaypoint {
            currentWptName = trimmed
        }

        if tag == "trkpt" || tag == "rtept" {
            if let lat = currentLat, let lon = currentLon {
                rawPoints.append(RawPoint(lat: lat, lon: lon, ele: currentEle))
            }
            isInPoint = false
        } else if tag == "wpt" {
            if let lat = currentLat, let lon = currentLon {
                let name = currentWptName ?? "Waypoint \(rawWaypoints.count + 1)"
                rawWaypoints.append(RawWaypoint(name: name, lat: lat, lon: lon, ele: currentEle))
            }
            isInWaypoint = false
        }
    }

    // MARK: - Process Points into Checkpoints

    private func buildResult(fileName: String, intervalKm: Double) throws -> GpxCourseResult {
        guard !rawPoints.isEmpty else {
            throw GpxParseError.noTrackpointsFound
        }

        var cumulativeDistance: Double = 0.0
        var totalGain: Double = 0.0
        var totalLoss: Double = 0.0
        var elevations: [Double] = []

        struct ProcessedPoint {
            let lat: Double
            let lon: Double
            let ele: Double
            let cumDist: Double
        }

        var processed: [ProcessedPoint] = []
        var prevPoint: RawPoint? = nil

        for pt in rawPoints {
            let ele = pt.ele ?? elevations.last ?? 0.0
            elevations.append(ele)

            if let prev = prevPoint {
                let deltaDist = Self.haversineMeters(lat1: prev.lat, lon1: prev.lon, lat2: pt.lat, lon2: pt.lon)
                cumulativeDistance += deltaDist

                let prevEle = prev.ele ?? ele
                let deltaEle = ele - prevEle
                if deltaEle > 0 {
                    totalGain += deltaEle
                } else {
                    totalLoss += abs(deltaEle)
                }
            }

            processed.append(ProcessedPoint(lat: pt.lat, lon: pt.lon, ele: ele, cumDist: cumulativeDistance))
            prevPoint = pt
        }

        guard cumulativeDistance > 100.0 else {
            throw GpxParseError.insufficientDistance
        }

        let minElev = elevations.min() ?? 0.0
        let maxElev = elevations.max() ?? 0.0
        let intervalM = max(500.0, intervalKm * 1000.0)

        // Generate checkpoints matching web/backend format
        var checkpoints: [CourseCheckpoint] = []
        let startElevation = processed.first?.ele ?? 0.0
        checkpoints.append(
            CourseCheckpoint(
                name: "Start",
                distanceMeters: 0.0,
                elevationMeters: round(startElevation),
                segmentGainMeters: 0.0,
                segmentLossMeters: 0.0
            )
        )

        var nextCpDist = intervalM
        var segGain: Double = 0.0
        var segLoss: Double = 0.0

        for i in 1..<processed.count {
            let curr = processed[i]
            let prev = processed[i - 1]

            let deltaEle = curr.ele - prev.ele
            if deltaEle > 0 {
                segGain += deltaEle
            } else {
                segLoss += abs(deltaEle)
            }

            if curr.cumDist >= nextCpDist {
                // Check if any named waypoint is nearby (within 600m)
                let nearbyWpt = rawWaypoints.first { wpt in
                    Self.haversineMeters(lat1: curr.lat, lon1: curr.lon, lat2: wpt.lat, lon2: wpt.lon) < 600.0
                }

                let cpName: String
                if let nearbyWpt {
                    cpName = nearbyWpt.name
                } else {
                    let kmVal = nextCpDist / 1000.0
                    cpName = (kmVal == floor(kmVal)) ? "KM \(Int(kmVal))" : String(format: "KM %.1f", kmVal)
                }

                checkpoints.append(
                    CourseCheckpoint(
                        name: cpName,
                        distanceMeters: round(curr.cumDist),
                        elevationMeters: round(curr.ele),
                        segmentGainMeters: round(segGain),
                        segmentLossMeters: round(segLoss)
                    )
                )

                segGain = 0.0
                segLoss = 0.0
                nextCpDist += intervalM
            }
        }

        // Add Finish checkpoint if route has remaining distance beyond last CP
        let finalDist = processed.last?.cumDist ?? cumulativeDistance
        let finalEle = processed.last?.ele ?? 0.0

        if let lastCp = checkpoints.last {
            if (finalDist - lastCp.distanceMeters) > 100.0 {
                checkpoints.append(
                    CourseCheckpoint(
                        name: "Finish",
                        distanceMeters: round(finalDist),
                        elevationMeters: round(finalEle),
                        segmentGainMeters: round(segGain),
                        segmentLossMeters: round(segLoss)
                    )
                )
            } else if lastCp.name != "Start" {
                checkpoints[checkpoints.count - 1] = CourseCheckpoint(
                    name: "Finish",
                    distanceMeters: round(finalDist),
                    elevationMeters: round(finalEle),
                    segmentGainMeters: lastCp.segmentGainMeters + round(segGain),
                    segmentLossMeters: lastCp.segmentLossMeters + round(segLoss)
                )
            }
        }

        return GpxCourseResult(
            fileName: fileName,
            totalDistanceKm: round((cumulativeDistance / 1000.0) * 10) / 10,
            totalElevationGainM: round(totalGain),
            totalElevationLossM: round(totalLoss),
            minElevationM: round(minElev),
            maxElevationM: round(maxElev),
            checkpoints: checkpoints,
            trackpointCount: rawPoints.count,
            waypointNames: rawWaypoints.map(\.name)
        )
    }

    // MARK: - Haversine Distance Formula

    static func haversineMeters(lat1: Double, lon1: Double, lat2: Double, lon2: Double) -> Double {
        let r = 6371000.0 // Earth radius in meters
        let dLat = (lat2 - lat1) * .pi / 180.0
        let dLon = (lon2 - lon1) * .pi / 180.0
        let a = sin(dLat / 2.0) * sin(dLat / 2.0) +
                cos(lat1 * .pi / 180.0) * cos(lat2 * .pi / 180.0) *
                sin(dLon / 2.0) * sin(dLon / 2.0)
        let c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))
        return r * c
    }

    // MARK: - Regex Fallback Parser for Malformed XML

    private func parseViaRegexFallback(data: Data, fileName: String, intervalKm: Double) -> GpxCourseResult? {
        guard let str = String(data: data, encoding: .utf8) else { return nil }
        let trkptPattern = #"<trkpt\s+[^>]*lat="([0-9.-]+)"[^>]*lon="([0-9.-]+)"[^>]*>(?:(?!<\/trkpt>).)*?(?:<ele>([0-9.-]+)<\/ele>)?.*?<\/trkpt>"#

        guard let regex = try? NSRegularExpression(pattern: trkptPattern, options: [.dotMatchesLineSeparators]) else {
            return nil
        }

        let nsString = str as NSString
        let matches = regex.matches(in: str, range: NSRange(location: 0, length: nsString.length))
        guard matches.count >= 2 else { return nil }

        rawPoints.removeAll()
        for match in matches {
            guard match.numberOfRanges >= 3 else { continue }
            let latStr = nsString.substring(with: match.range(at: 1))
            let lonStr = nsString.substring(with: match.range(at: 2))
            var eleVal: Double? = nil
            if match.numberOfRanges >= 4 && match.range(at: 3).location != NSNotFound {
                eleVal = Double(nsString.substring(with: match.range(at: 3)))
            }
            if let lat = Double(latStr), let lon = Double(lonStr) {
                rawPoints.append(RawPoint(lat: lat, lon: lon, ele: eleVal))
            }
        }

        return try? buildResult(fileName: fileName, intervalKm: intervalKm)
    }
}
