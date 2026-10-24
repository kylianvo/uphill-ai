package ai.uphill.app.core.networking
interface TokenStore {
    fun read(): String?

    fun write(token: String?)
}

class MemoryTokenStore(private var token: String? = null) : TokenStore {
    override fun read() = token

    override fun write(token: String?) {
        this.token = token
    }
}
