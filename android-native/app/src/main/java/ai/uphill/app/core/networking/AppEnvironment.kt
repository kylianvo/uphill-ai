package ai.uphill.app.core.networking
object AppEnvironment {
    const val production = "https://api.uphill-ai.io.vn"
    const val staging = "https://staging-api.uphill-ai.io.vn"
    const val local = "http://10.0.2.2:8000"

    fun baseURL(debug: Boolean, override: String?): String =
        if (debug) override ?: local else production
}
