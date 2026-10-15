package ai.uphill.app.app

import ai.uphill.app.core.auth.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.plan.TrainingNavigation
import ai.uphill.app.designsystem.LocalReduceMotion
import ai.uphill.app.designsystem.UH
import ai.uphill.app.feature.auth.*
import ai.uphill.app.feature.coaching.*
import ai.uphill.app.feature.gear.GearScreen
import ai.uphill.app.feature.goal.GoalScreen
import ai.uphill.app.feature.integrations.IntegrationsScreen
import ai.uphill.app.feature.knowledge.KnowledgeScreen
import ai.uphill.app.feature.launch.LaunchScreen
import ai.uphill.app.feature.me.MeScreen
import ai.uphill.app.feature.nutrition.NutritionScreen
import ai.uphill.app.feature.onboarding.OnboardingScreen
import ai.uphill.app.feature.onboarding.WelcomeScreen
import ai.uphill.app.feature.pace.PaceScreen
import ai.uphill.app.feature.plan.PlanScreen
import ai.uphill.app.feature.racehistory.RaceHistoryScreen
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import androidx.navigation.compose.*
import kotlinx.coroutines.launch

@Composable
fun RootNav(container: AppContainer) {
    val session by container.session.state.collectAsState()
    val lang by container.language.collectAsState()
    val scope = rememberCoroutineScope()
    val transitionDuration = if (LocalReduceMotion.current) 0 else 350
    when (val value = session) {
        SessionState.Restoring -> LaunchScreen()
        SessionState.SignedOut -> {
            val model: SignInViewModel =
                viewModel(
                    factory =
                        viewModelFactory {
                            initializer { SignInViewModel(container.auth, container.session) }
                        }
                )
            SignInScreen(model)
        }
        is SessionState.SignedIn ->
            key(value.user.id) {
                val user = value.user
                var onboarded by remember(user.id) { mutableStateOf(user.onboardingComplete) }
                fun finishOnboarding() {
                    onboarded = true
                    scope.launch {
                        try {
                            container.session.updateUser(container.auth.me())
                        } catch (_: Exception) {}
                    }
                }
                if (!onboarded) {
                    var child by remember { mutableStateOf<String?>(null) }
                    var startedSetup by remember { mutableStateOf(false) }
                    if (!startedSetup)
                        WelcomeScreen(
                            onStart = { startedSetup = true },
                            onNotNow = ::finishOnboarding,
                        )
                    else if (child == null)
                        OnboardingScreen(
                            container.api,
                            user,
                            lang,
                            ::finishOnboarding,
                            onNavigate = { child = it },
                            onClose = { startedSetup = false },
                        )
                    else
                        Column {
                            TextButton(onClick = { child = null }) { Text(L("Back")) }
                            when (child) {
                                "integrations",
                                "watch" ->
                                    IntegrationsScreen(container.api, user, lang, { child = it })
                                "racehistory",
                                "race-history" ->
                                    RaceHistoryScreen(container.api, user, lang, { child = it })
                                else ->
                                    OnboardingScreen(
                                        container.api,
                                        user,
                                        lang,
                                        ::finishOnboarding,
                                        onNavigate = { child = it },
                                    )
                            }
                        }
                } else {
                    val nav = rememberNavController()
                    val backStack by nav.currentBackStackEntryAsState()
                    val route = backStack?.destination?.route ?: "plan"
                    val tabs =
                        listOf(
                            "plan" to Icons.Outlined.DateRange,
                            "coach" to Icons.Outlined.ChatBubbleOutline,
                            "me" to Icons.Outlined.Person,
                        ) +
                            if (user.isCoach) listOf("athletes" to Icons.Outlined.Groups)
                            else emptyList()
                    var selectedTab by rememberSaveable { mutableStateOf("plan") }
                    LaunchedEffect(route) {
                        if (tabs.any { it.first == route }) selectedTab = route
                    }
                    val navigate: (String) -> Unit = { target ->
                        if (target == "back") nav.popBackStack()
                        else {
                            val destination =
                                when (target) {
                                    "watch" -> "integrations"
                                    "profile" -> "me"
                                    "race_history",
                                    "race-history" -> "racehistory"
                                    "new_plan",
                                    "newPlan" -> "setup"
                                    else -> target
                                }
                            val actual =
                                when {
                                    target.startsWith("workout/") -> {
                                        TrainingNavigation.workoutId.value =
                                            target.substringAfter('/').toIntOrNull()
                                        "plan"
                                    }
                                    target.startsWith("profile/") -> {
                                        TrainingNavigation.profileSection.value =
                                            target.substringAfter('/')
                                        "me"
                                    }
                                    else -> destination
                                }
                            nav.navigate(actual) { launchSingleTop = true }
                        }
                    }
                    Scaffold(
                        bottomBar = {
                            NavigationBar(containerColor = Color.White, tonalElevation = 0.dp) {
                                tabs.forEach { (tab, icon) ->
                                    NavigationBarItem(
                                        colors =
                                            NavigationBarItemDefaults.colors(
                                                selectedIconColor = UH.accentInk,
                                                selectedTextColor = UH.accentInk,
                                                indicatorColor = Color.Transparent,
                                                unselectedIconColor = UH.secondary,
                                                unselectedTextColor = UH.secondary,
                                            ),
                                        selected = selectedTab == tab,
                                        onClick = {
                                            nav.navigate(tab) {
                                                popUpTo(nav.graph.startDestinationId) {
                                                    saveState = true
                                                }
                                                launchSingleTop = true
                                                restoreState = true
                                            }
                                        },
                                        icon = { Icon(icon, contentDescription = null) },
                                        label = {
                                            Text(
                                                L(
                                                    when (tab) {
                                                        "plan" -> "Plan"
                                                        "coach" -> "Coach"
                                                        "athletes" -> "Athletes"
                                                        else -> "Me"
                                                    }
                                                )
                                            )
                                        },
                                    )
                                }
                            }
                        },
                        topBar = {
                            if (
                                route !in tabs.map { it.first } &&
                                    route !in
                                        listOf("goal", "gear", "nutrition", "pace", "knowledge")
                            )
                                TextButton(onClick = { nav.popBackStack() }) { Text(L("Back")) }
                        },
                    ) { padding ->
                        Box(Modifier.padding(padding)) {
                            NavHost(
                                navController = nav,
                                startDestination = "plan",
                                enterTransition = {
                                    if (targetState.destination.route in tabs.map { it.first })
                                        fadeIn(tween(0))
                                    else slideInHorizontally(tween(transitionDuration)) { it }
                                },
                                exitTransition = { fadeOut(tween(transitionDuration)) },
                                popEnterTransition = { fadeIn(tween(transitionDuration)) },
                                popExitTransition = {
                                    slideOutHorizontally(tween(transitionDuration)) { it }
                                },
                            ) {
                                composable("plan") {
                                    PlanScreen(container.api, user, lang, navigate)
                                }
                                composable("coach") {
                                    ai.uphill.app.feature.chat.ChatScreen(
                                        container.api,
                                        user,
                                        lang,
                                        navigate,
                                    )
                                }
                                composable("me") {
                                    MeScreen(
                                        container.api,
                                        user,
                                        lang,
                                        navigate,
                                        onLanguage = {
                                            scope.launch { container.settings.language(it) }
                                        },
                                        onEnvironment = {
                                            scope.launch {
                                                container.auth.logout()
                                                container.session.signOut()
                                                container.settings.environment(it)
                                            }
                                        },
                                        onLogout = {
                                            scope.launch {
                                                container.auth.logout()
                                                container.session.signOut()
                                            }
                                        },
                                        onUser = container.session::updateUser,
                                    )
                                }
                                composable("setup") {
                                    OnboardingScreen(
                                        container.api,
                                        user,
                                        lang,
                                        { nav.popBackStack("plan", false) },
                                        navigate,
                                        newPlan = true,
                                    )
                                }
                                composable("goal") {
                                    GoalScreen(container.api, user, lang, navigate)
                                }
                                composable("gear") {
                                    GearScreen(container.api, user, lang, navigate)
                                }
                                composable("nutrition") {
                                    NutritionScreen(container.api, user, lang, navigate)
                                }
                                composable("pace") {
                                    PaceScreen(container.api, user, lang, navigate)
                                }
                                composable("knowledge") {
                                    KnowledgeScreen(container.api, user, lang, navigate)
                                }
                                composable("integrations") {
                                    IntegrationsScreen(container.api, user, lang, navigate)
                                }
                                composable("racehistory") {
                                    RaceHistoryScreen(container.api, user, lang, navigate)
                                }
                                composable("athletes") {
                                    AthletesScreen(container.api, user, lang, navigate)
                                }
                                composable("athlete/{id}") { entry ->
                                    entry.arguments?.getString("id")?.toIntOrNull()?.let { id ->
                                        if (user.isCoach)
                                            CoachedAthleteScreen(
                                                container.api,
                                                user,
                                                lang,
                                                navigate,
                                                id,
                                            )
                                    }
                                }
                                composable("athlete-plan/{id}") { entry ->
                                    entry.arguments?.getString("id")?.toIntOrNull()?.let { id ->
                                        if (user.isCoach)
                                            PlanScreen(
                                                container.api,
                                                user,
                                                lang,
                                                navigate,
                                                athleteId = id,
                                            )
                                    }
                                }
                            }
                        }
                    }
                }
            }
    }
}
