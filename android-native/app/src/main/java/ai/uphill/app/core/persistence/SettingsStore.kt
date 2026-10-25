package ai.uphill.app.core.persistence

import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.map

private val Context.uphillSettings by preferencesDataStore("uphill_settings")

class SettingsStore(context: Context) {
    private val store = context.applicationContext.uphillSettings
    val language = store.data.map { it[stringPreferencesKey("language")] ?: "en" }
    val environment = store.data.map { it[stringPreferencesKey("environment")] }

    suspend fun language(value: String) {
        require(value in setOf("en", "vi"))
        store.edit { it[stringPreferencesKey("language")] = value }
    }

    suspend fun environment(value: String) {
        store.edit { it[stringPreferencesKey("environment")] = value }
    }
}
