from enum import Enum, auto

class TweakID(Enum):
    # tweaks page
    PosterBoard = auto()
    Templates = auto()
    StatusBar = auto()
    IconThemes = auto()

    # springboard
    LockScreenFootnote = auto()
    WatchOSCompatibility = auto()
    AirDropDisableTimeLimit = auto()
    SBDontLockAfterCrash = auto()
    SBDontDimOrLockOnAC = auto()
    SBHideLowPowerAlerts = auto()
    SBHideACPower = auto()
    SBNeverBreadcrumb = auto()
    SBShowSupervisionTextOnLockScreen = auto()
    AirplaySupport = auto()
    SBMinimumLockscreenIdleTime = auto()
    SBAlwaysShowSystemApertureInSnapshots = auto()
    HideDICompletely = auto()
    SBShowAuthenticationEngineeringUI = auto()
    UseFloatingTabBar = auto()
    SBDisableIconParallax = auto()
    SBHideSearchAffordance = auto()

    # mobilegestalt (ported from leminlimez/Nugget; not supported on iOS 26.2+)
    DynamicIsland = auto()
    SupportsDynamicIsland = auto()
    ModelName = auto()
    BootChime = auto()
    EnableLGLPM = auto()
    DisableLGLPM = auto()
    RdarFix = auto()
    ChargeLimit = auto()
    CollisionSOS = auto()
    TapToWake = auto()
    CameraButton = auto()
    Parallax = auto()
    StageManager = auto()
    iPadOS = auto()
    iPadOSCacheData = auto()
    iPadApps = auto()
    Shutter = auto()
    Pencil = auto()
    ActionButton = auto()
    InternalStorage = auto()
    InternalInstall = auto()
    SRD = auto()
    AOD = auto()
    AODVibrancy = auto()
    # NOTE: in leminlimez/Nugget this tweak lives in load_eligibility()
    # (eligibility page); the tweak definition itself is verbatim.
    AIGestalt = auto()

    # eligibility (ported verbatim from leminlimez/Nugget's load_eligibility();
    # removed by GoldenNugget, re-added here using Nugget's original code)
    EUEnabler = auto()
    AIEligibility = auto()
    AIFeatureFlags = auto()
    AIFeatureFlagsUI = auto()
    SpoofModel = auto()
    SpoofHardware = auto()
    SpoofCPU = auto()
    CreateBRFolders = auto()

    # feature flags (ported from leminlimez/Nugget; removed by GoldenNugget,
    # re-added here using Nugget's original flag definitions)
    ClockAnim = auto()
    Lockscreen = auto()
    PhotoUI = auto()
    AI = auto()
    KioskMode = auto()

    # internal
    SBBuildNumber = auto()
    RTL = auto()
    LTR = auto()
    SBIconVisibility = auto()
    # NOTE: MetalForceHudEnabled was removed (audit B28) — upstream Nugget's
    # load_internal() defines it, but this fork carries no spec for it.
    iMessageDiagnosticsEnabled = auto()
    IDSDiagnosticsEnabled = auto()
    VCDiagnosticsEnabled = auto()
    AccessoryDeveloperEnabled = auto()
    KeyFlick = auto()
    DisableThermal = auto()

    DisableSecondsHand = auto()
    DisableSearchingWebsites = auto()
    ShowButtonHints = auto()

    AppStoreDebug = auto()
    NotesDebugMode = auto()
    BKDigitizerVisualizeTouches = auto()
    BKHideAppleLogoOnLaunch = auto()
    EnableWakeGestureHaptic = auto()
    PlaySoundOnPaste = auto()
    AnnounceAllPastes = auto()

    # liquid glass — Round 6 (2026-10-02, per user order): 71 audited candidates
    # added for pre-beta developer release. All unverified on device.
    # See ~/workspace/riset/AUDIT-KANDIDAT-BARU.md for audit details.
    SolariumForceFallback = auto()
    # Deprecated alias for backward compat with old presets (pre-4.0)
    ForceSolariumFallback = SolariumForceFallback
    # UIKit variant — re-added 2026-10-21 per user order: key string verified
    # present in iOS 27.0.1 (24A446); device-negative on 26.6.1, untested on 27.
    UISolariumForceFallback = auto()
    DisableSolariumSwiftUI = auto()
    GlassLegibility2 = auto()
    SolariumFeatureFlags = auto()
    GranularSpringBoard = auto()
    LGLPMGestalt = auto()
    DisallowGlassTime = auto()
    DisableGlassDock = auto()
    FlatIconsEverywhere = auto()
    DisableWidgetSpecular = auto()
    DisableDockSpecular = auto()
    DisableFolderSpecular = auto()
    ExcludeClearGlassShadows = auto()
    ExcludeDockShadow = auto()
    ExcludeSearchShadow = auto()
    DisableOuterRefraction = auto()
    DisableSolariumHDR = auto()
    DisableSpecularMotion = auto()
    DisableCompactChrome = auto()
    DisableSpecularEverywhere = auto()
    SuppressDICompletely = auto()
    # Blurr Motion (2026-10-03): the single candidate from the DesignLibrary
    # dossier whose key string is attested in the 23G83 binary
    # (~/workspace/riset/wave11/DOSSIER-BLURR-MOTION.md). Normal tweak, no
    # badge: unverified status lives in its description, not a lock.
    BlurrMotion = auto()
    # status bar visual (non-glass)
    StatusBarOverrides = auto()
    ShowSystemServices = auto()
    ShowBatteryPercentage = auto()
    # lock screen custom (non-glass)
    CustomLockDate = auto()
    # notifications (non-glass, Apple keys)
    NotifDisplayStyle = auto()
    NotifPreview = auto()
    NotifScheduled = auto()
    NotifSummarize = auto()
    NotifAnnounce = auto()
    NotifHighlights = auto()
    NotifAlertType = auto()
    NotifGrouping = auto()
    NotifVisibility = auto()
    NotifPriority = auto()
    # home screen non-glass
    DisableParallax = auto()
    HideSearchAffordance = auto()
    IconVisibility = auto()
    DisableClockSeconds = auto()
    # keyboard (non-glass)
    KbAutocorrect = auto()
    KbPrediction = auto()
    KbPredBar = auto()
    KbGestureIntro = auto()
    KbAutoLists = auto()
    # siri classic (non-glass)
    SiriEnabled = auto()
    SiriDataSharing = auto()
    SiriAutoPunct = auto()
    SiriVoiceTrigger = auto()
    SiriTriggerPhrase = auto()
    SiriSpeakerTTS = auto()
    SiriDeclined = auto()
    SiriVocab = auto()
    # animation (non-glass)
    AnimDragCoeff = auto()

    # risky (ported from leminlimez/Nugget's load_risky())
    DisableOTAFile = auto()
    CustomResolution = auto()

    # daemons
    Daemons = auto()
    ClearScreenTimeAgentPlist = auto()

    # Partial Liquid Glass disable + new menu tweaks (2026-10-17,
    # research batch lg-partial-26: binary-attested keys from iOS 26.1
    # dyld, audited in ~/workspace/riset/audit-kandidat-lg-26.md).
    # K1/K3/K4/K5/K6 = verified-structure; the rest structural-hypothesis
    # (device-proven NOT required per user 2026-10-17 — honest grade in
    # each registry description instead).
    # --- verified-structure (partial LG disable) ---
    DisallowGlassLockScreen = auto()        # K1 SBDisallowGlassLockScreen
    IOS18LockScreenLook = auto()            # SBDisallowGlassButtons (structure-verified: CSProminentButtonView.disallowGlassButtons reader; pure new tweak, user order 2026-10-18)
    DisableHSGlassExterior = auto()         # K3 SolariumEnableHomeScreenExteriorEffects=false
    DisableDockGlassExterior = auto()       # K4 SolariumEnableDockExteriorEffects=false
    DisableKeyboardGlassExterior = auto()   # K5 SolariumEnableKeyboardExteriorEffects=false
    DisableSolariumFocusForeground = auto() # K6 SolariumDisableFocusForegroundEffects
    # --- structural-hypothesis: Liquid Glass menu ---
    SolariumForceDarkShadow = auto()
    SolariumHighlightWhite = auto()
    # --- K8 (deep-audit PROMOTE): Solarium pref-family keys, binary-attested ---
    SolariumBackgroundFilter = auto()
    SolariumTextFrost = auto()
    SolariumUseDisplayAngle = auto()
    # --- iOS 27 scan candidates (2026-10-22, verified per-subcache in
    # 23G82 + 24A446; see ~/workspace/riset/ios27/SUPPORT-LISTS.md) ---
    SolariumForceEnhancedSpeculars = auto()  # 27-only: field forcesEnhancedSpeculars in the DesignLibrary settings struct
    FloatingContentViewBGFills = auto()      # UISolariumFloatingContentViewEnableBackgroundFills (both firmwares)
    SolariumCornerRadius = auto()            # corner pair as ONE tweak (radius + SolariumInsetsAndCornerRadiusEnabled)
    # --- structural-hypothesis: Lock Screen menu ---
    SBShowLegalTextOnLockScreen = auto()
    SBDontLockEver = auto()
    SBDisableAutoDim = auto()
    # --- structural-hypothesis: Home Screen menu ---
    SBDisableIconFlyInAnimation = auto()
    SBDisableLiveIcons = auto()
    SBDisableParallaxOnPageControl = auto()
    SBEnableHomeScreenWallpaperDimming = auto()
    # --- structural-hypothesis: Notifications menu ---
    SBHideNotifications = auto()
    SBShowNotificationsInAlwaysOn = auto()
    SBAllowNotificationsDuringScreenSharing = auto()
    # --- structural-hypothesis: Dynamic Island menu (mutually exclusive pair) ---
    SBAlwaysRenderApertureOnGPU = auto()
    SBNeverRenderApertureOnGPU = auto()
    # --- structural-hypothesis: Status Bar menu ---
    SBShowRSSI = auto()
    SBShowRingerState = auto()
    SBShowBatteryLevel = auto()
    # --- structural-hypothesis: SpringBoard/System menu ---
    SBDisableAttentionAwareness = auto()
    SBDisableProximity = auto()
    SBDisableHomeButton = auto()
    SBDisableIdleSleep = auto()
