package ai.uphill.app.designsystem

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.interaction.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.dp

@Composable
fun PrimaryButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    shape: Shape = RoundedCornerShape(UH.Radius.control),
    colors: ButtonColors =
        ButtonDefaults.buttonColors(
            containerColor = UH.accent,
            contentColor = UH.buttonInk,
            disabledContainerColor = UH.accent.copy(alpha = .45f),
            disabledContentColor = UH.buttonInk,
        ),
    elevation: ButtonElevation? = null,
    border: BorderStroke? = null,
    contentPadding: PaddingValues = ButtonDefaults.ContentPadding,
    interactionSource: MutableInteractionSource? = null,
    content: @Composable RowScope.() -> Unit,
) {
    val interactions = interactionSource ?: remember { MutableInteractionSource() }
    val pressed by interactions.collectIsPressedAsState()
    val reduced = LocalReduceMotion.current
    val scale by
        animateFloatAsState(
            if (pressed && !reduced) 0.97f else 1f,
            spring(dampingRatio = 1f, stiffness = 320f),
            label = "button press",
        )
    androidx.compose.material3.Button(
        onClick,
        modifier.heightIn(min = 48.dp).scale(scale).alpha(if (pressed && reduced) .8f else 1f),
        enabled,
        shape,
        colors,
        elevation,
        border,
        contentPadding,
        interactions,
        content,
    )
}

@Composable
fun SecondaryButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    shape: Shape = RoundedCornerShape(UH.Radius.control),
    colors: ButtonColors =
        ButtonDefaults.outlinedButtonColors(
            containerColor = androidx.compose.ui.graphics.Color.Black.copy(alpha = .06f),
            contentColor = UH.ink,
        ),
    elevation: ButtonElevation? = null,
    border: BorderStroke? = null,
    contentPadding: PaddingValues = ButtonDefaults.ContentPadding,
    interactionSource: MutableInteractionSource? = null,
    content: @Composable RowScope.() -> Unit,
) {
    val interactions = interactionSource ?: remember { MutableInteractionSource() }
    val pressed by interactions.collectIsPressedAsState()
    val reduced = LocalReduceMotion.current
    val scale by
        animateFloatAsState(
            if (pressed && !reduced) 0.97f else 1f,
            spring(dampingRatio = 1f, stiffness = 320f),
            label = "button press",
        )
    androidx.compose.material3.OutlinedButton(
        onClick,
        modifier.heightIn(min = 48.dp).scale(scale).alpha(if (pressed && reduced) .8f else 1f),
        enabled,
        shape,
        colors,
        elevation,
        border,
        contentPadding,
        interactions,
        content,
    )
}
