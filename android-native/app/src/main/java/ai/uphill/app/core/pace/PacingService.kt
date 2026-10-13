package ai.uphill.app.core.pace

import ai.uphill.app.core.goal.RaceBenchmark
import ai.uphill.app.core.networking.*
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

class PacingService(private val api: APIClient) {
    suspend fun calculate(request: PacingRequest): List<PacedCheckpoint> =
        try {
            api.send(
                Endpoint(
                    "POST",
                    "/api/coach/calculate-pacing",
                    JSONCoding.json.encodeToJsonElement(request),
                )
            )
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            PacingCalculator.calculate(
                request.checkpoints,
                request.targetTimeMins,
                request.targetFlatPaceMinKm,
                request.splitBias ?: 0.0,
                request.runnerWeightKg ?: 68.0,
            )
        }

    @Serializable
    private data class Benchmarks(val matched: Boolean, val results: List<RaceBenchmark>? = null)

    suspend fun benchmarks(name: String, distanceKm: Double): List<RaceBenchmark> =
        try {
            api.send<Benchmarks>(
                    Endpoint(
                        "GET",
                        "/api/coach/pace-strategy/benchmarks",
                        query = mapOf("name" to name, "distance_km" to distanceKm.toString()),
                        requiresAuth = false,
                    )
                )
                .let { if (it.matched) it.results.orEmpty() else emptyList() }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            emptyList()
        }
}
