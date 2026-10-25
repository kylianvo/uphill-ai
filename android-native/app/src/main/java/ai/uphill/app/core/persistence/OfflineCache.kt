package ai.uphill.app.core.persistence

import ai.uphill.app.core.networking.JSONCoding
import java.io.File
import kotlinx.serialization.*

class OfflineCache(val directory: File) {
    init {
        directory.mkdirs()
    }

    inline fun <reified T> save(key: String, value: T) {
        val target = File(directory, "$key.json")
        val temp = File(directory, "$key.tmp")
        temp.writeText(JSONCoding.json.encodeToString(value))
        check(temp.renameTo(target)) { "Unable to save offline cache" }
    }

    inline fun <reified T> load(key: String): T? =
        runCatching { JSONCoding.json.decodeFromString<T>(File(directory, "$key.json").readText()) }
            .getOrNull()

    fun clear() {
        directory.listFiles()?.forEach { it.delete() }
    }
}
