package ai.uphill.app.core.localization

import ai.uphill.app.core.networking.*
import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import kotlinx.serialization.json.*

/** Source keys stay shared with the iOS string catalog. */
@Composable
fun L(key: String, vararg args: Any): String {
    val context = LocalContext.current
    val keys =
        remember(context.assets) {
            JSONCoding.json
                .parseToJsonElement(
                    context.assets.open("string_keys.json").bufferedReader().use { it.readText() }
                )
                .jsonObject
        }
    val name = keys[key]?.jsonPrimitive?.content ?: return key
    val id = context.resources.getIdentifier(name, "string", context.packageName)
    return if (id != 0) context.getString(id, *args) else key
}

fun localizedError(context: Context, error: Throwable): String {
    val key = error.message ?: "Something went wrong. Please try again."
    val keys =
        JSONCoding.json
            .parseToJsonElement(
                context.assets.open("string_keys.json").bufferedReader().use { it.readText() }
            )
            .jsonObject
    val name = keys[key]?.jsonPrimitive?.content ?: return key
    val id = context.resources.getIdentifier(name, "string", context.packageName)
    return if (id != 0) context.getString(id) else key
}
