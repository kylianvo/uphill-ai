package ai.uphill.app.core.chat

import ai.uphill.app.core.networking.JSONCoding
import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.serialization.json.*

private val Context.chatData by preferencesDataStore("uphill_chat")

class ChatHistory(context: Context) {
    private val data = context.applicationContext.chatData

    suspend fun load(userId: Int, planId: Int): List<ChatMessage> {
        val raw = data.data.first()[stringPreferencesKey("${userId}_$planId")] ?: return emptyList()
        return runCatching {
                JSONCoding.json.parseToJsonElement(raw).jsonArray.map {
                    ChatMessage.decode(it.jsonObject)
                }
            }
            .getOrDefault(emptyList())
    }

    suspend fun save(userId: Int, planId: Int, messages: List<ChatMessage>) {
        data.edit {
            it[stringPreferencesKey("${userId}_$planId")] =
                JsonArray(messages.takeLast(50).map { message -> message.encode() }).toString()
        }
    }

    suspend fun clear() {
        data.edit { it.clear() }
    }
}
