package ai.uphill.app.feature.chat

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.chat.*
import ai.uphill.app.core.networking.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.util.UUID
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.json.*

data class ChatState(
    val messages: List<ChatMessage> = emptyList(),
    val busy: Boolean = false,
    val status: String = "",
    val error: Throwable? = null,
    val hasMore: Boolean = false,
    val clarify: List<String> = emptyList(),
    val proposals: Map<Int, JsonObject> = emptyMap(),
    val sources: JsonObject? = null,
    val retryOf: String? = null,
)

class ChatViewModel(
    private val api: APIClient,
    private val user: User,
    private val history: ChatHistory,
) : ViewModel() {
    private val service = ChatService(api)
    private val mutable = MutableStateFlow(ChatState())
    val state = mutable.asStateFlow()
    private var planId = 0
    private var stream: Job? = null

    init {
        viewModelScope.launch {
            try {
                planId =
                    (api.element(Endpoint("GET", "/api/coach/active-plan")).jsonObject["plan"]
                            as? JsonObject)
                        ?.get("id")
                        ?.jsonPrimitive
                        ?.intOrNull ?: 0
            } catch (_: APIError) {}
            mutable.update { it.copy(messages = history.load(user.id, planId)) }
            try {
                val thread = service.thread()
                mutable.update {
                    it.copy(
                        messages = thread.messages,
                        hasMore = thread.hasMore,
                        proposals = thread.proposals,
                    )
                }
                cache()
            } catch (e: APIError) {
                mutable.update { it.copy(error = e) }
            }
        }
    }

    fun send(text: String, lang: String, retryOf: String? = null) {
        if (mutable.value.busy || (retryOf == null && (text.isBlank() || text.length > 2000)))
            return
        val request = UUID.randomUUID().toString()
        mutable.update { old ->
            old.copy(
                messages =
                    if (retryOf == null)
                        old.messages + ChatMessage(UUID.randomUUID().toString(), null, "user", text)
                    else old.messages,
                busy = true,
                status = "",
                error = null,
                clarify = emptyList(),
                retryOf = request,
            )
        }
        stream =
            viewModelScope.launch {
                var assistantId: String? = null
                fun editAssistant(transform: (ChatMessage) -> ChatMessage) {
                    if (assistantId == null) {
                        assistantId = UUID.randomUUID().toString()
                        mutable.update {
                            it.copy(
                                messages =
                                    it.messages +
                                        ChatMessage(assistantId!!, null, "assistant", "", request)
                            )
                        }
                    }
                    mutable.update { state ->
                        state.copy(
                            messages =
                                state.messages.map {
                                    if (it.id == assistantId) transform(it) else it
                                }
                        )
                    }
                }
                try {
                    service
                        .stream(request, if (retryOf == null) text else null, retryOf, lang)
                        .collect { event ->
                            val d = event.data
                            when (event.type) {
                                "status" -> mutable.update { it.copy(status = d.s("step")) }
                                "token" ->
                                    editAssistant { it.copy(content = it.content + d.s("text")) }
                                "citations" ->
                                    editAssistant {
                                        it.copy(
                                            citations =
                                                (d["citations"] as? JsonArray)
                                                    .orEmpty()
                                                    .mapNotNull { x -> x as? JsonObject }
                                        )
                                    }
                                "tool_result" ->
                                    editAssistant { it.copy(tools = it.tools + ChatTool.decode(d)) }
                                "clarify" ->
                                    mutable.update {
                                        it.copy(
                                            clarify =
                                                (d["options"] as? JsonArray).orEmpty().map { x ->
                                                    x.jsonPrimitive.content
                                                }
                                        )
                                    }
                                "done" -> {
                                    val id = d["message_id"]?.jsonPrimitive?.intOrNull
                                    editAssistant { it.copy(numericId = id, interrupted = false) }
                                    mutable.update { it.copy(retryOf = null) }
                                }
                                "error" -> throw Exception(d.s("message").ifBlank { d.s("code") })
                            }
                        }
                    cache()
                } catch (e: Exception) {
                    editAssistant { it.copy(interrupted = true) }
                    if (e !is CancellationException) mutable.update { it.copy(error = e) }
                    cache()
                } finally {
                    mutable.update { it.copy(busy = false, status = "") }
                }
            }
    }

    fun stop() {
        stream?.cancel()
    }

    fun older() {
        viewModelScope.launch {
            val before = mutable.value.messages.firstOrNull()?.numericId ?: return@launch
            try {
                val thread = service.thread(before)
                mutable.update {
                    it.copy(
                        messages = thread.messages + it.messages,
                        hasMore = thread.hasMore,
                        proposals = it.proposals + thread.proposals,
                    )
                }
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            }
        }
    }

    fun clear() {
        if (mutable.value.busy) return
        viewModelScope.launch {
            try {
                service.clear()
                mutable.value = ChatState()
                cache()
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            }
        }
    }

    fun sources(id: Int) {
        viewModelScope.launch {
            try {
                mutable.update { it.copy(sources = service.sources(id)) }
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            }
        }
    }

    fun closeSources() {
        mutable.update { it.copy(sources = null) }
    }

    fun feedback(id: Int, value: Int) {
        viewModelScope.launch {
            try {
                service.feedback(id, value)
                mutable.update { state ->
                    state.copy(
                        messages =
                            state.messages.map {
                                if (it.numericId == id) it.copy(feedback = value) else it
                            }
                    )
                }
                cache()
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            }
        }
    }

    fun refreshProposal(id: Int) {
        viewModelScope.launch {
            repeat(80) {
                try {
                    val proposal = service.proposal(id)
                    mutable.update { it.copy(proposals = it.proposals + (id to proposal)) }
                    if (proposal.s("status") != "generating") return@launch
                } catch (e: APIError) {
                    mutable.update { it.copy(error = e) }
                }
                delay(3000)
            }
            mutable.update {
                it.copy(error = Exception("This is taking longer than usual. Please try again."))
            }
        }
    }

    fun actProposal(id: Int, apply: Boolean) {
        viewModelScope.launch {
            try {
                if (apply) service.apply(id) else service.discard(id)
                val proposal = service.proposal(id)
                mutable.update { it.copy(proposals = it.proposals + (id to proposal)) }
            } catch (e: APIError.Http) {
                if (e.status == 409) refreshProposal(id)
                mutable.update { it.copy(error = e) }
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            }
        }
    }

    private suspend fun cache() {
        if (api.tokenStore.read() != null) history.save(user.id, planId, mutable.value.messages)
    }
}
