package ai.uphill.app.core.auth

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class SessionStoreTest {
    private fun fixture(name: String) = javaClass.classLoader!!.getResource(name)!!.readText()

    @Test
    fun `auth fixtures decode identity without retaining API keys`() {
        val response = JSONCoding.json.decodeFromString<AuthResponse>(fixture("auth_login.json"))
        assertEquals("fixture-session-token", response.sessionToken)
        assertEquals("ios-fixtures@uphill.ai", response.user.email)
        assertFalse(
            JSONCoding.json
                .encodeToString(User.serializer(), response.user)
                .contains("gemini_api_key")
        )
        assertEquals(
            response.user.id,
            JSONCoding.json.decodeFromString<User>(fixture("auth_me.json")).id,
        )
    }

    @Test
    fun `transport failure restores only previously cached user`() = runTest {
        val user = JSONCoding.json.decodeFromString<User>(fixture("auth_me.json"))
        val tokens = MemoryTokenStore("valid")
        val session = SessionStore(tokens, { user }, {}, {})
        session.restore { throw APIError.Transport(java.io.IOException()) }
        assertEquals(user, (session.state.value as SessionState.SignedIn).user)
        assertEquals("valid", tokens.read())
    }

    @Test
    fun `expired token clears user cache and signs out`() = runTest {
        var cleared = false
        val tokens = MemoryTokenStore("expired")
        val session = SessionStore(tokens, { null }, {}, { cleared = true })
        session.restore { throw APIError.Unauthorized() }
        assertEquals(SessionState.SignedOut, session.state.value)
        assertNull(tokens.read())
        assertTrue(cleared)
    }

    @Test
    fun `server failure keeps the token and permits a successful restore retry`() = runTest {
        val user = JSONCoding.json.decodeFromString<User>(fixture("auth_me.json"))
        val tokens = MemoryTokenStore("valid")
        var cleared = false
        val session = SessionStore(tokens, { user }, {}, { cleared = true })
        session.restore { throw APIError.Http(503) }
        assertEquals(SessionState.Restoring, session.state.value)
        assertEquals("valid", tokens.read())
        assertFalse(cleared)
        assertTrue(session.restoreError.value is APIError.Http)
        session.restore { user }
        assertNull(session.restoreError.value)
        assertEquals(user, (session.state.value as SessionState.SignedIn).user)
    }

    @Test
    fun `network failure without cache retains the token for retry`() = runTest {
        val tokens = MemoryTokenStore("valid")
        val session = SessionStore(tokens, { null }, {}, {})
        session.restore { throw APIError.Transport(java.io.IOException()) }
        assertEquals(SessionState.Restoring, session.state.value)
        assertEquals("valid", tokens.read())
    }

    @Test
    fun `restore cannot revive a signed out account`() = runTest {
        val user = JSONCoding.json.decodeFromString<User>(fixture("auth_me.json"))
        val tokens = MemoryTokenStore("old-token")
        var saved = false
        val session = SessionStore(tokens, { user }, { saved = true }, {})
        session.restore {
            session.signOut()
            user
        }
        assertEquals(SessionState.SignedOut, session.state.value)
        assertFalse(saved)
        assertNull(tokens.read())
    }

    @Test
    fun `old restore failure cannot expire a replacement session`() = runTest {
        val response = JSONCoding.json.decodeFromString<AuthResponse>(fixture("auth_login.json"))
        val tokens = MemoryTokenStore("old-token")
        val session = SessionStore(tokens, { null }, {}, {})
        session.restore {
            session.signIn(response)
            throw APIError.Unauthorized()
        }
        assertEquals(response.sessionToken, tokens.read())
        assertEquals(SessionState.SignedIn(response.user), session.state.value)
        assertNull(session.restoreError.value)
    }

    @Test
    fun `login stores new token and sign out clears local data`() {
        var cleared = false
        val tokens = MemoryTokenStore()
        val session = SessionStore(tokens, { null }, {}, { cleared = true })
        val response = JSONCoding.json.decodeFromString<AuthResponse>(fixture("auth_login.json"))
        session.signIn(response)
        assertEquals("fixture-session-token", tokens.read())
        assertTrue(session.state.value is SessionState.SignedIn)
        session.signOut()
        assertNull(tokens.read())
        assertTrue(cleared)
    }
}
