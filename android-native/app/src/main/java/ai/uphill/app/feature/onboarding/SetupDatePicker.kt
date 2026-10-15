package ai.uphill.app.feature.onboarding

import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filterNotNull

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun SetupDatePicker(
    value: LocalDate?,
    minimum: LocalDate,
    maximum: LocalDate? = null,
    onSelect: (LocalDate) -> Unit,
) {
    val dates =
        remember(minimum, maximum) {
            object : SelectableDates {
                override fun isSelectableDate(utcTimeMillis: Long): Boolean {
                    val day =
                        Instant.ofEpochMilli(utcTimeMillis).atZone(ZoneOffset.UTC).toLocalDate()
                    return day >= minimum && (maximum == null || day <= maximum)
                }

                override fun isSelectableYear(year: Int) =
                    year >= minimum.year && (maximum == null || year <= maximum.year)
            }
        }
    val initial =
        (value ?: minimum).coerceAtLeast(minimum).let {
            if (maximum == null) it else it.coerceAtMost(maximum)
        }
    val picker =
        rememberDatePickerState(
            initialSelectedDateMillis =
                initial.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli(),
            selectableDates = dates,
        )
    val currentOnSelect by rememberUpdatedState(onSelect)
    LaunchedEffect(picker) {
        snapshotFlow { picker.selectedDateMillis }
            .filterNotNull()
            .distinctUntilChanged()
            .collect { millis ->
                // Material DatePicker dates are UTC days, not instants in the device's time zone.
                currentOnSelect(Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate())
            }
    }
    OutlinedCard(
        Modifier.fillMaxWidth().testTag("setup.calendar"),
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, UH.line),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
    ) {
        DatePicker(
            picker,
            modifier = Modifier.fillMaxWidth(),
            title = null,
            headline = null,
            showModeToggle = false,
            colors = DatePickerDefaults.colors(containerColor = Color.White),
        )
    }
}
