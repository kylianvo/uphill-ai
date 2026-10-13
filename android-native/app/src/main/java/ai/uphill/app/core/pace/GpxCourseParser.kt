package ai.uphill.app.core.pace

import java.io.ByteArrayInputStream
import javax.xml.parsers.SAXParserFactory
import kotlin.math.*
import org.xml.sax.Attributes
import org.xml.sax.helpers.DefaultHandler

object GpxCourseParser {
    private data class Point(
        val lat: Double,
        val lon: Double,
        val ele: Double?,
        val name: String? = null,
    )

    fun haversineMeters(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val dLat = (lat2 - lat1) * PI / 180
        val dLon = (lon2 - lon1) * PI / 180
        val a =
            sin(dLat / 2).pow(2) +
                cos(lat1 * PI / 180) * cos(lat2 * PI / 180) * sin(dLon / 2).pow(2)
        return 6371000 * 2 * atan2(sqrt(a), sqrt((1 - a).coerceAtLeast(0.0)))
    }

    fun parse(data: ByteArray, fileName: String, intervalKm: Double = 5.0): GpxCourseResult {
        require(data.isNotEmpty()) { "GPX file contains no data." }
        val points = mutableListOf<Point>()
        val waypoints = mutableListOf<Point>()
        val handler =
            object : DefaultHandler() {
                var lat: Double? = null
                var lon: Double? = null
                var ele: Double? = null
                var name: String? = null
                var waypoint = false
                val text = StringBuilder()

                override fun startElement(
                    uri: String?,
                    localName: String?,
                    qName: String?,
                    a: Attributes,
                ) {
                    text.clear()
                    when (qName?.substringAfter(':')?.lowercase()) {
                        "trkpt",
                        "rtept",
                        "wpt" -> {
                            lat = a.getValue("lat")?.toDoubleOrNull()
                            lon = a.getValue("lon")?.toDoubleOrNull()
                            ele = null
                            name = null
                            waypoint = qName.substringAfter(':').equals("wpt", true)
                        }
                    }
                }

                override fun characters(ch: CharArray, start: Int, length: Int) {
                    text.append(ch, start, length)
                }

                override fun endElement(uri: String?, localName: String?, qName: String?) {
                    when (qName?.substringAfter(':')?.lowercase()) {
                        "ele" -> ele = text.toString().trim().toDoubleOrNull()
                        "name" -> if (waypoint) name = text.toString().trim()
                        "trkpt",
                        "rtept",
                        "wpt" -> {
                            val a = lat
                            val b = lon
                            if (a != null && b != null) {
                                val p = Point(a, b, ele, name)
                                if (waypoint) waypoints += p else points += p
                            }
                        }
                    }
                }
            }
        try {
            val factory = SAXParserFactory.newInstance()
            factory.isNamespaceAware = false
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false)
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false)
            factory.newSAXParser().parse(ByteArrayInputStream(data), handler)
        } catch (e: Exception) {
            // Mirror the iOS recovery path for truncated or otherwise malformed track XML.
            val fallback =
                Regex(
                        "<(?:trkpt|rtept)\\b([^>]*)>(.*?)</(?:trkpt|rtept)>",
                        RegexOption.DOT_MATCHES_ALL,
                    )
                    .findAll(data.toString(Charsets.UTF_8))
                    .mapNotNull { m ->
                        fun attr(k: String) =
                            Regex("$k=[\"']([^\"']+)[\"']")
                                .find(m.groupValues[1])
                                ?.groupValues
                                ?.get(1)
                                ?.toDoubleOrNull()
                        val a = attr("lat")
                        val b = attr("lon")
                        if (a != null && b != null)
                            Point(
                                a,
                                b,
                                Regex("<ele>([^<]+)</ele>")
                                    .find(m.groupValues[2])
                                    ?.groupValues
                                    ?.get(1)
                                    ?.toDoubleOrNull(),
                            )
                        else null
                    }
                    .toList()
            require(fallback.size >= 2) { "Failed to parse GPX XML: ${e.message}" }
            points.clear()
            points += fallback
        }
        require(points.isNotEmpty()) { "No valid trackpoints found in the GPX file." }
        val elevations = mutableListOf<Double>()
        val distances = mutableListOf<Double>()
        var distance = 0.0
        var gain = 0.0
        var loss = 0.0
        points.forEachIndexed { i, p ->
            val ele = p.ele ?: elevations.lastOrNull() ?: 0.0
            elevations += ele
            if (i > 0) {
                val prev = points[i - 1]
                distance += haversineMeters(prev.lat, prev.lon, p.lat, p.lon)
                val delta = ele - (prev.ele ?: ele)
                if (delta > 0) gain += delta else loss += abs(delta)
            }
            distances += distance
        }
        require(distance > 100) { "Route distance is too short to generate course checkpoints." }
        val cps = mutableListOf(CourseCheckpoint("Start", 0.0, round(elevations.first()), 0.0, 0.0))
        val interval = max(500.0, intervalKm * 1000)
        var next = interval
        var sg = 0.0
        var sl = 0.0
        for (i in 1 until points.size) {
            val delta = elevations[i] - elevations[i - 1]
            if (delta > 0) sg += delta else sl += abs(delta)
            if (distances[i] >= next) {
                val p = points[i]
                val near =
                    waypoints.firstOrNull { haversineMeters(p.lat, p.lon, it.lat, it.lon) < 600 }
                val name =
                    near?.name
                        ?: if (next / 1000 == floor(next / 1000)) "KM ${(next/1000).toInt()}"
                        else "KM %.1f".format(next / 1000)
                cps +=
                    CourseCheckpoint(
                        name,
                        round(distances[i]),
                        round(elevations[i]),
                        round(sg),
                        round(sl),
                    )
                sg = 0.0
                sl = 0.0
                next += interval
            }
        }
        val finalDistance = round(distances.last())
        val finalElevation = round(elevations.last())
        val last = cps.last()
        if (distance - last.distanceMeters > 100)
            cps += CourseCheckpoint("Finish", finalDistance, finalElevation, round(sg), round(sl))
        else if (last.name != "Start")
            cps[cps.lastIndex] =
                last.copy(
                    name = "Finish",
                    distanceMeters = finalDistance,
                    elevationMeters = finalElevation,
                    segmentGainMeters = last.segmentGainMeters + round(sg),
                    segmentLossMeters = last.segmentLossMeters + round(sl),
                )
        return GpxCourseResult(
            fileName,
            round(distance / 1000 * 10) / 10,
            round(gain),
            round(loss),
            round(elevations.min()),
            round(elevations.max()),
            cps,
            points.size,
            waypoints.mapIndexed { i, p -> p.name ?: "Waypoint ${i+1}" },
        )
    }
}
