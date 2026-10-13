import Foundation

struct RaceFormError: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}

func safeRaceResultURL(_ value: String?) -> URL? {
    guard let value, let components = URLComponents(string: value),
          ["http", "https"].contains(components.scheme?.lowercased() ?? ""),
          let host = components.host, !host.isEmpty,
          components.user == nil, components.password == nil else { return nil }
    return components.url
}

struct ManualRaceDraft {
    var raceName = ""
    var date = Date()
    var discipline = "trail"
    var distance = ""
    var elevation = ""
    var duration = ""
    var isDnf = false
    var location = ""
    var bib = ""
    var resultUrl = ""
    var userNote = ""
    var rankOverall = ""
    var totalOverall = ""
    var rankGender = ""
    var totalGender = ""
    var rankAgeGroup = ""
    var totalAgeGroup = ""

    init(result: RaceResult? = nil) {
        guard let result else { return }
        raceName = result.raceName; discipline = result.discipline
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd"
        date = formatter.date(from: result.raceDate) ?? Date()
        distance = String(result.distanceKm)
        elevation = result.elevationGainM.map { String($0) } ?? ""
        duration = result.finishTimeSec.map(DistanceBadge.formatTime) ?? ""
        isDnf = result.isDnf; location = result.location ?? ""; bib = result.bib ?? ""
        resultUrl = result.resultUrl ?? ""; userNote = result.userNote ?? ""
        rankOverall = result.rankOverall.map(String.init) ?? ""
        totalOverall = result.totalOverall.map(String.init) ?? ""
        rankGender = result.rankGender.map(String.init) ?? ""
        totalGender = result.totalGender.map(String.init) ?? ""
        rankAgeGroup = result.rankAgeGroup.map(String.init) ?? ""
        totalAgeGroup = result.totalAgeGroup.map(String.init) ?? ""
    }

    func payload() throws -> ManualResultPayload {
        func text(_ value: String, label: String, limit: Int) throws -> String? {
            let result = value.trimmingCharacters(in: .whitespacesAndNewlines)
            guard result.count <= limit else { throw RaceFormError(message: "\(label) is too long.") }
            return result.isEmpty ? nil : result
        }
        func integer(_ value: String, label: String) throws -> Int? {
            let value = value.trimmingCharacters(in: .whitespacesAndNewlines)
            if value.isEmpty { return nil }
            guard let number = Int(value), number > 0 else { throw RaceFormError(message: "Enter a positive whole number for \(label).") }
            return number
        }
        func ranks(_ rank: String, _ total: String, label: String) throws -> (Int?, Int?) {
            let r = try integer(rank, label: "\(label) rank"), t = try integer(total, label: "\(label) finishers")
            if let r, let t, r > t { throw RaceFormError(message: "\(label) rank cannot exceed the number of finishers.") }
            return (r, t)
        }
        guard let name = try text(raceName, label: "Race name", limit: 200),
              ["trail", "road"].contains(discipline) else { throw RaceFormError(message: "Enter the race name and discipline.") }
        guard let km = Double(distance), km.isFinite, km > 0, km <= 1000 else { throw RaceFormError(message: "Enter a distance between 0 and 1,000 km.") }
        let gain: Double?
        if elevation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { gain = nil }
        else {
            guard let number = Double(elevation), number.isFinite, number >= 0 else { throw RaceFormError(message: "Elevation must be zero or a positive number.") }
            gain = number
        }
        var seconds: Int? = nil
        if !isDnf {
            let components = duration.trimmingCharacters(in: .whitespacesAndNewlines).split(separator: ":", omittingEmptySubsequences: false)
            let numbers = components.compactMap { Int($0) }
            guard (2...3).contains(components.count), numbers.count == components.count,
                  numbers.allSatisfy({ $0 >= 0 }), numbers.last! < 60,
                  (numbers.count == 2 || numbers[1] < 60), numbers[0] <= 9999 else { throw RaceFormError(message: "Enter finish time as h:mm:ss or mm:ss.") }
            seconds = numbers.count == 3 ? numbers[0] * 3600 + numbers[1] * 60 + numbers[2] : numbers[0] * 60 + numbers[1]
            guard seconds! > 0 else { throw RaceFormError(message: "Finish time must be greater than zero.") }
        }
        let link = try text(resultUrl, label: "Result link", limit: 2048)
        if let link, safeRaceResultURL(link) == nil { throw RaceFormError(message: "Use an http or https result link without credentials.") }
        let overall = try ranks(rankOverall, totalOverall, label: "Overall")
        let gender = try ranks(rankGender, totalGender, label: "Gender")
        let age = try ranks(rankAgeGroup, totalAgeGroup, label: "Age group")
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd"
        return ManualResultPayload(raceName: name, raceDate: formatter.string(from: date), discipline: discipline,
            distanceKm: km, elevationGainM: gain, finishTimeSec: seconds, isDnf: isDnf,
            rankOverall: overall.0, totalOverall: overall.1,
            location: try text(location, label: "Location", limit: 200), resultUrl: link,
            rankGender: gender.0, totalGender: gender.1, rankAgeGroup: age.0, totalAgeGroup: age.1,
            bib: try text(bib, label: "Bib", limit: 100), userNote: try text(userNote, label: "Race note", limit: 2000))
    }
}

extension ManualResultPayload {
    func patchChanges() throws -> [String: JSONValue] {
        var value = try JSONDecoder().decode([String: JSONValue].self, from: JSONCoding.encoder.encode(self))
        for key in ["elevation_gain_m", "finish_time_sec", "rank_overall", "total_overall", "rank_gender", "total_gender", "rank_age_group", "total_age_group", "location", "bib", "result_url", "user_note"] where value[key] == nil {
            value[key] = .null
        }
        return value
    }
}
