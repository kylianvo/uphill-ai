package ai.uphill.app.core.coaching

import ai.uphill.app.core.networking.*
import androidx.lifecycle.ViewModelStore
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class CoachedProfileViewModelTest {
    @Test
    fun failedSaveRetainsProfileAndDoesNotDismissThenRetryAndGeneralNoteSucceed() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val server = MockWebServer()
        val store = ViewModelStore()
        val fixture =
            javaClass.classLoader!!.getResource("coaching_athlete_profile.json")!!.readText()
        server.enqueue(MockResponse().setBody(fixture))
        server.enqueue(MockResponse().setBody("{\"notes\":[]}"))
        server.enqueue(
            MockResponse().setResponseCode(500).setBody("{\"detail\":\"Try again later\"}")
        )
        server.enqueue(
            MockResponse().setBody(fixture.replace("\"resting_hr\": 52", "\"resting_hr\": 55"))
        )
        server.enqueue(
            MockResponse()
                .setBody(
                    """{"id":99,"athlete_id":7,"coach_id":39,"target_type":"general","target_id":null,"note":"Keep easy days easy."}"""
                )
        )
        server.start()
        try {
            val model =
                CoachedProfileViewModel(
                    CoachingService(
                        APIClient({ server.url("/").toString() }, MemoryTokenStore("t"))
                    ),
                    7,
                )
            store.put("profile", model)
            suspend fun settled() =
                withContext(Dispatchers.Default) {
                    withTimeout(5000) { model.state.first { !it.busy } }
                }
            model.load()
            assertEquals(52, settled().profile!!.restingHr)
            assertEquals("/api/coaching/athletes/7/profile", server.takeRequest().path)
            assertEquals("general", server.takeRequest().requestUrl!!.queryParameter("target_type"))
            var dismissed = false
            model.save(buildJsonObject { put("resting_hr", 55) }) { dismissed = true }
            assertNotNull(settled().error)
            assertFalse(dismissed)
            assertEquals(52, model.state.value.profile!!.restingHr)
            assertEquals("PATCH", server.takeRequest().method)
            model.save(buildJsonObject { put("resting_hr", 55) }) { dismissed = true }
            assertEquals(55, settled().profile!!.restingHr)
            assertTrue(dismissed)
            assertNull(model.state.value.error)
            val patch = server.takeRequest()
            assertEquals("/api/coaching/athletes/7/profile", patch.path)
            assertEquals("{\"resting_hr\":55}", patch.body.readUtf8())
            var cleared = false
            model.post("  Keep easy days easy.  ") { cleared = true }
            assertEquals("Keep easy days easy.", settled().notes.single().note)
            assertTrue(cleared)
            val request = server.takeRequest()
            assertEquals("/api/coaching/athletes/7/notes", request.requestUrl!!.encodedPath)
            val body = JSONCoding.json.parseToJsonElement(request.body.readUtf8()).jsonObject
            assertEquals("general", body["target_type"]!!.jsonPrimitive.content)
            assertEquals("Keep easy days easy.", body["note"]!!.jsonPrimitive.content)
            assertTrue(body["target_id"] == null || body["target_id"] == JsonNull)
        } finally {
            val job = store.get("profile")?.viewModelScope?.coroutineContext?.get(Job)
            store.clear()
            job?.join()
            server.shutdown()
            Dispatchers.resetMain()
        }
    }
}
