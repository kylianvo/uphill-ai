package ai.uphill.app

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.networking.MemoryTokenStore
import ai.uphill.app.feature.pace.PaceScreen
import ai.uphill.app.core.localization.localizedText
import android.content.ContentValues
import android.content.res.Configuration
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import java.util.Locale
import android.os.Build
import android.provider.MediaStore
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

/** Exercises the actual system document picker and content resolver, not a mock URI. */
class GpxImportFlowTest {
    @get:Rule val ui = createComposeRule()

    @Test
    fun importsDownloadedGpxThroughSystemPickerAndRemovesCourse() = importCourse("en")

    @Test
    fun importsDownloadedGpxWithVietnameseControls() = importCourse("vi")

    private fun importCourse(lang: String) {
        assumeTrue(Build.VERSION.SDK_INT >= 29)
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val resolver = instrumentation.targetContext.contentResolver
        val name = "uphill_fixture_course.gpx"
        val uri =
            requireNotNull(
                resolver.insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                    ContentValues().apply {
                        put(MediaStore.MediaColumns.DISPLAY_NAME, name)
                        put(MediaStore.MediaColumns.MIME_TYPE, "application/gpx+xml")
                        put(MediaStore.MediaColumns.RELATIVE_PATH, "Download/")
                        put(MediaStore.MediaColumns.IS_PENDING, 1)
                    },
                )
            )
        val server = MockWebServer()
        try {
            resolver.openOutputStream(uri)!!.bufferedWriter().use {
                it.write(
                    """<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>
                    <trkpt lat="22.30" lon="103.80"><ele>1500</ele></trkpt>
                    <trkpt lat="22.31" lon="103.81"><ele>1600</ele></trkpt>
                    <trkpt lat="22.32" lon="103.82"><ele>1550</ele></trkpt>
                    <trkpt lat="22.33" lon="103.83"><ele>1650</ele></trkpt>
                    </trkseg></trk></gpx>"""
                )
            }
            resolver.update(uri, ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }, null, null)
            server.enqueue(MockResponse().setHeader("Content-Type", "application/json").setBody("{}"))
            server.start()
            val api = APIClient({ server.url("/").toString() }, MemoryTokenStore("fixture-only"))
            val localizedContext = instrumentation.targetContext.createConfigurationContext(
                Configuration(instrumentation.targetContext.resources.configuration).apply { setLocale(Locale.forLanguageTag(lang)) }
            )
            fun label(key: String) = localizedText(localizedContext, key)
            ui.setContent {
                val configuration = Configuration(LocalConfiguration.current).apply { setLocale(Locale.forLanguageTag(lang)) }
                val registry = requireNotNull(LocalActivityResultRegistryOwner.current)
                CompositionLocalProvider(
                    LocalContext provides localizedContext,
                    LocalConfiguration provides configuration,
                    LocalActivityResultRegistryOwner provides registry,
                ) {
                    AppFixture { PaceScreen(api, User(7, "fixture@example.com", "Runner"), lang, {}) }
                }
            }
            fun capture(state: String) {
                val args = InstrumentationRegistry.getArguments()
                if (args.getString("captureEvidence") != "true") return
                ui.waitForIdle()
                val variant = args.getString("captureVariant") ?: "normal"
                val directory = "/sdcard/Download/uphill-evidence/$variant"
                instrumentation.uiAutomation.executeShellCommand("mkdir -p $directory").use {
                    java.io.FileInputStream(it.fileDescriptor).readBytes()
                }
                instrumentation.uiAutomation.executeShellCommand("screencap -p $directory/pace-$state-$lang.png").use {
                    java.io.FileInputStream(it.fileDescriptor).readBytes()
                }
            }
            capture("course")
            ui.onNodeWithTag("pace.importGpx").performScrollTo().performClick()
            var document: AccessibilityNodeInfo? = null
            ui.waitUntil(15000) {
                document = findDocument(instrumentation.uiAutomation.rootInActiveWindow, name)
                document != null
            }
            var clickTarget = document
            while (clickTarget != null && !clickTarget!!.isClickable) clickTarget = clickTarget!!.parent
            assertTrue("Downloaded course is selectable", clickTarget?.performAction(AccessibilityNodeInfo.ACTION_CLICK) == true)
            ui.waitUntil(15000) {
                ui.onAllNodesWithText(name, substring = true).fetchSemanticsNodes().isNotEmpty()
            }
            ui.onNodeWithText("+200 m D+", substring = true).assertExists()
            ui.onNodeWithContentDescription(label("Distance (km)")).assertIsNotEnabled().assertTextContains("4.5")
            ui.onNodeWithContentDescription(label("Gain (m D+)")).assertIsNotEnabled().assertTextContains("200")
            org.junit.Assert.assertEquals(42.25f, ui.onNodeWithTag("pace.target").fetchSemanticsNode()
                .config[androidx.compose.ui.semantics.SemanticsProperties.ProgressBarRangeInfo].current, .01f)
            capture("gpx")
            ui.onNodeWithTag("pace.controls").performScrollTo()
            capture("controls")
            ui.onNodeWithTag("pace.target")
                .performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.SetProgress) { it(50f) }
            ui.onNodeWithText("1 km").performScrollTo().performClick()
            ui.waitUntil(15000) {
                ui.onAllNodesWithText("4 CPs", substring = true).fetchSemanticsNodes().isNotEmpty()
            }
            org.junit.Assert.assertEquals(50f, ui.onNodeWithTag("pace.target").fetchSemanticsNode()
                .config[androidx.compose.ui.semantics.SemanticsProperties.ProgressBarRangeInfo].current, .01f)
            ui.onNodeWithContentDescription(label("Remove GPX file")).performScrollTo().performClick()
            ui.onNodeWithContentDescription(label("Distance (km)")).assertIsEnabled()
            ui.onNodeWithContentDescription(label("Gain (m D+)")).assertIsEnabled()
            ui.onNodeWithText(name, substring = true).assertDoesNotExist()
        } finally {
            resolver.delete(uri, null, null)
            server.shutdown()
        }
    }

    private fun findDocument(node: AccessibilityNodeInfo?, name: String): AccessibilityNodeInfo? {
        if (node == null) return null
        if (node.text?.toString() == name) return node
        for (i in 0 until node.childCount) {
            findDocument(node.getChild(i), name)?.let { return it }
        }
        return null
    }
}
