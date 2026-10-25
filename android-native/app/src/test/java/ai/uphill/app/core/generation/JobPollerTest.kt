package ai.uphill.app.core.generation

import ai.uphill.app.core.networking.APIError
import java.io.IOException
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

class JobPollerTest {
    @Test
    fun doneAfterGeneratingReturnsSnapshot() = runTest {
        var calls = 0
        val poller =
            JobPoller(
                status = { if (++calls < 3) JobStatus("generating") else JobStatus("done") },
                sleep = {},
            )
        assertEquals(JobOutcome.Done(null), poller.wait("j"))
        assertEquals(3, calls)
    }

    @Test
    fun missingJobIsLost() = runTest {
        assertEquals(
            JobOutcome.Lost,
            JobPoller(status = { throw APIError.Http(404) }, sleep = {}).wait("j"),
        )
    }

    @Test
    fun fiveConsecutiveTransportFailuresStopPolling() = runTest {
        var calls = 0
        val result =
            JobPoller(
                    status = {
                        calls++
                        throw APIError.Transport(IOException())
                    },
                    sleep = {},
                )
                .wait("j")
        assertEquals(JobOutcome.Failed(JobPoller.offlineMessage), result)
        assertEquals(5, calls)
    }

    @Test
    fun successfulPollResetsTransportFailureCount() = runTest {
        var calls = 0
        val result =
            JobPoller(
                    status = {
                        calls++
                        when {
                            calls == 5 -> JobStatus("generating")
                            calls == 10 -> JobStatus("done")
                            else -> throw APIError.Transport(IOException())
                        }
                    },
                    sleep = {},
                )
                .wait("j")
        assertEquals(JobOutcome.Done(null), result)
        assertEquals(10, calls)
    }

    @Test
    fun timeoutUsesBoundedNumberOfAttempts() = runTest {
        var calls = 0
        assertEquals(
            JobOutcome.Failed(JobPoller.slowMessage),
            JobPoller(
                    status = {
                        calls++
                        JobStatus("generating")
                    },
                    timeoutMs = 6000,
                    sleep = {},
                )
                .wait("j"),
        )
        assertEquals(3, calls)
    }

    @Test
    fun serverErrorPreservesExplanation() = runTest {
        assertEquals(
            JobOutcome.Failed("Quota exceeded"),
            JobPoller(status = { JobStatus("error", error = "Quota exceeded") }, sleep = {})
                .wait("j"),
        )
    }
}
