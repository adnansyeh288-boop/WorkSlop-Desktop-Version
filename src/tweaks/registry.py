"""Single source of truth for the plist-based tweaks.

Every tweak's definition (id, section, title, plist location, key, default
value, UI kind) lives here exactly once. ``tweak_loader`` builds the runtime
instances from these specs and the iOS tweaks page renders its rows from
them — adding a tweak means adding one entry here.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import QT_TRANSLATE_NOOP

from .basic_plist_locations import FileLocation
from .tweak_names import TweakID


class Section(Enum):
    LIQUID_GLASS = "Liquid Glass"
    SPRINGBOARD = "SpringBoard"
    FEATURE_FLAGS = "Feature Flags"
    INTERNAL = "Internal Options"


class Kind(Enum):
    SWITCH = "switch"   # boolean toggle
    TEXT = "text"       # free-form text value
    NUMBER = "number"   # numeric value


# Feature (page) key each registry Section belongs to. Feeds HotLoad's
# FEATURE_TWEAKS so every registry tweak automatically joins its feature;
# the Sidebar uses the same keys to know which page owns a section.
SECTION_FEATURES: dict[Section, str] = {
    Section.LIQUID_GLASS: "Liquid Glass",
    Section.SPRINGBOARD: "Springboard",
    Section.FEATURE_FLAGS: "Feature Flags",
    Section.INTERNAL: "Internal",
}


@dataclass(frozen=True)
class TweakSpec:
    id: TweakID
    section: Section
    title: str
    location: FileLocation
    key: str
    value: any = True          # value written when the tweak is enabled
    kind: Kind = Kind.SWITCH
    min_value: float = 0       # NUMBER kind only
    max_value: float = 999     # NUMBER kind only
    step: float = 1.0          # NUMBER kind only; not integral = decimal input
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    iphone_only: bool = False
    ipad_only: bool = False
    factory: Optional[Callable[[], object]] = None  # overrides BasicPlistTweak
    description: Optional[str] = None  # detailed "what it does" tooltip
    requires_gestalt: bool = False  # True = MobileGestalt capability decision is mandatory
    disabled: bool = False  # True = tweak is cut off: never loaded, never applied, never rendered
    excludes: tuple = ()  # TweakIDs that must be turned off when this one is
                          # turned on (mutually-exclusive pairs, e.g. RTL/LTR).
                          # Enforced by set_tweak_enabled() in tweaks.py.


def _t(id_: TweakID, section: Section, title: str, location: FileLocation,
       key: str, description: str = "", **kwargs) -> TweakSpec:
    # QT_TRANSLATE_NOOP marks the title for pyside6-lupdate; the actual
    # translation happens at render time (translators are not installed yet
    # when this module is imported).
    return TweakSpec(id=id_, section=section,
                     title=QT_TRANSLATE_NOOP("Nugget", title),
                     description=QT_TRANSLATE_NOOP("Nugget", description) if description else None,
                     location=location, key=key, **kwargs)


def _watchos_compatibility():
    from .tweak_classes import AdvancedPlistTweak
    return AdvancedPlistTweak(
        FileLocation.nanoregistry,
        keyValues={
            "IOS_PAIRING_EOL_MIN_PAIRING_COMPATIBILITY_VERSION_CHIPIDS": "",
            "maxPairingCompatibilityVersion": 37,
            "lastRestoreIdentifier": "CD97EEB8-BCD2-486B-BC13-C384E6B916C4",  # not sure if this is needed
            "minPairingCompatibilityVersionWithChipID": 1,
            "lastRestoreIdentifier_state": 0,
            "AdvertisingIdentifierSeed": "85E70251-1960-4DA0-A321-B68AC118FAB5",  # this prolly isn't needed either
            "minPairingCompatibilityVersion": 1
        })


GP = FileLocation.globalPreferences


# The five registry Feature Flags specs (ClockAnim, Lockscreen, PhotoUI,
# AI, KioskMode) stay removed from the active product registry — their
# delivery channel is dead for iOS 26.6.1 and the audit kill list names
# them explicitly. The single v4 SolariumFeatureFlags row returned
# verbatim with the Liquid Glass restoration (2026-10-03) as a direct
# SPECS entry capped at max_version 26.1. The TweakID members for the
# removed five remain only as tombstones in
# src/tweaks/capabilities.py::REMOVED_TWEAK_IDS; old presets naming them
# resolve to removed/skipped, never to a FeatureFlags payload.
_FF_SPECS: tuple[TweakSpec, ...] = ()

SPECS: tuple[TweakSpec, ...] = (
    # --- Liquid Glass ---
    # The Liquid Glass section carries the WorkSlop v4 set restored
    # verbatim (user order 2026-10-03): the v4 specs below are byte-
    # identical to src/tweaks/registry.py @ 4f44415 (same key, file
    # location, value/type, version gates). Blurr Motion is a separate
    # 2026-10-03 addition, not part of the v4 set. Reset/write semantics
    # follow v4 (device_manager LiquidGlass reset: GP + UIKit + per-app
    # files; iOS 26 zero-byte contents, iOS 27+ empty plist).

    # --- SpringBoard ---
    # === Partial LG batch: SpringBoard menus (2026-10-17, lg-partial-26) ===
    # Binary-attested SB* keys from the iOS 26.1 dyld (audit:
    # ~/workspace/riset/audit-kandidat-lg-26.md). All structural-hypothesis.
    # SBDisableIconFlyInAnimation is wired ONCE here even though the audit
    # lists it under both Home Screen and Animation menus.
    _t(TweakID.SBShowLegalTextOnLockScreen, Section.SPRINGBOARD, "Show Legal Text on Lock Screen",
       GP, "SBShowLegalTextOnLockScreen",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Shows the legal text on the Lock Screen (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDontLockEver, Section.SPRINGBOARD, "Never Auto-Lock",
       GP, "SBDontLockEver",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Prevents the device from auto-locking (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableAutoDim, Section.SPRINGBOARD, "Disable Auto-Dim",
       GP, "SBDisableAutoDim",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables display auto-dimming (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableIconFlyInAnimation, Section.SPRINGBOARD, "Disable Icon Fly-In Animation",
       GP, "SBDisableIconFlyInAnimation",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables the icon fly-in animation on the Home Screen (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableLiveIcons, Section.SPRINGBOARD, "Disable Live Icons",
       GP, "SBDisableLiveIcons",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables live Home Screen icons (Clock/Calendar) so they render static (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableParallaxOnPageControl, Section.SPRINGBOARD, "Disable Page-Control Parallax",
       GP, "SBDisableParallaxOnPageControl",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables the parallax effect on the Home Screen page dots (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBEnableHomeScreenWallpaperDimming, Section.SPRINGBOARD, "Home Screen Wallpaper Dimming",
       GP, "SBEnableHomeScreenWallpaperDimming",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Enables wallpaper dimming on the Home Screen (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBHideNotifications, Section.SPRINGBOARD, "Hide Notifications",
       GP, "SBHideNotifications",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Hides notifications (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBShowNotificationsInAlwaysOn, Section.SPRINGBOARD, "Show Notifications in Always-On",
       GP, "SBShowNotificationsInAlwaysOn",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Shows notifications on the Always-On display (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBAllowNotificationsDuringScreenSharing, Section.SPRINGBOARD, "Allow Notifications During Screen Sharing",
       GP, "SBAllowNotificationsDuringScreenSharing",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Allows notifications to appear while screen sharing (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    # Dynamic Island GPU render pair — mutually exclusive: the excludes
    # tuple is enforced by set_tweak_enabled() (same pattern as RTL/LTR).
    # The descriptions also warn never to enable both at once.
    _t(TweakID.SBAlwaysRenderApertureOnGPU, Section.SPRINGBOARD, "Always Render Dynamic Island on GPU",
       GP, "SBAlwaysRenderSystemApertureFillOnGPU",
       min_version="26.0", iphone_only=True,
       description=QT_TRANSLATE_NOOP("Nugget", "Forces the Dynamic Island fill to always render on the GPU (structural-hypothesis: binary-attested key). WARNING: never enable together with 'Never Render Dynamic Island on GPU' — they are mutually exclusive. Unverified — needs device test."),
       excludes=(TweakID.SBNeverRenderApertureOnGPU,)),
    _t(TweakID.SBNeverRenderApertureOnGPU, Section.SPRINGBOARD, "Never Render Dynamic Island on GPU",
       GP, "SBNeverRenderSystemApertureFillOnGPU",
       min_version="26.0", iphone_only=True,
       description=QT_TRANSLATE_NOOP("Nugget", "Never renders the Dynamic Island fill on the GPU (structural-hypothesis: binary-attested key). WARNING: never enable together with 'Always Render Dynamic Island on GPU' — they are mutually exclusive. Unverified — needs device test."),
       excludes=(TweakID.SBAlwaysRenderApertureOnGPU,)),
    _t(TweakID.SBShowRSSI, Section.SPRINGBOARD, "Show Numeric Signal (RSSI)",
       GP, "SBShowRSSI",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Shows the numeric cellular signal strength (RSSI) in the status bar (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBShowRingerState, Section.SPRINGBOARD, "Show Ringer State",
       GP, "SBShowRingerState",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Shows the ringer state in the status bar (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBShowBatteryLevel, Section.SPRINGBOARD, "Show Battery Level",
       GP, "SBShowBatteryLevel",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Shows the battery level in the status bar (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableAttentionAwareness, Section.SPRINGBOARD, "Disable Attention Awareness",
       GP, "SBDisableAttentionAwareness",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables attention-awareness features (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableProximity, Section.SPRINGBOARD, "Disable Proximity Sensor",
       GP, "SBDisableProximity",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables the proximity sensor (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SBDisableHomeButton, Section.SPRINGBOARD, "Disable Home Button",
       GP, "SBDisableHomeButton",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables the Home button (structural-hypothesis: binary-attested key). Harmless no-op on iPhones without a Home button. Unverified — needs device test.")),
    _t(TweakID.SBDisableIdleSleep, Section.SPRINGBOARD, "Disable Idle Sleep",
       GP, "SBDisableIdleSleep",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables idle sleep (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.LockScreenFootnote, Section.SPRINGBOARD, "Lock Screen Footnote Text",
       FileLocation.footnote, "LockScreenFootnote", value="", kind=Kind.TEXT,
       description=QT_TRANSLATE_NOOP("Nugget", "Sets custom text shown at the bottom of the Lock Screen below the time. Long text is cut off — keep it short. Leave empty to remove.")),
    _t(TweakID.WatchOSCompatibility, Section.SPRINGBOARD, "Allow pairing with any watchOS version",
       FileLocation.nanoregistry, "", factory=_watchos_compatibility,
       description=QT_TRANSLATE_NOOP("Nugget", "Removes the minimum watchOS pairing check in NanoRegistry so you can pair an Apple Watch running any watchOS version with your iPhone.")),
    _t(TweakID.AirDropDisableTimeLimit, Section.SPRINGBOARD, "Disable AirDrop Time Limit for Everyone Option",
       FileLocation.airdrop, "OverrideTimeLimitEveryoneMode",
       description=QT_TRANSLATE_NOOP("Nugget", "Unlocks the hidden 'Everyone' AirDrop receiving option that would normally be limited to a 10-minute time window.")),
    _t(TweakID.SBDontLockAfterCrash, Section.SPRINGBOARD, "Disable Lock After Respring",
       FileLocation.springboard, "SBDontLockAfterCrash",
       description=QT_TRANSLATE_NOOP("Nugget", "Prevents the screen from locking right after a respring — the phone won't ask for a passcode immediately after the UI reloads.")),
    _t(TweakID.SBDontDimOrLockOnAC, Section.SPRINGBOARD, "Disable Screen Dimming While Charging",
       FileLocation.springboard, "SBDontDimOrLockOnAC",
       description=QT_TRANSLATE_NOOP("Nugget", "Stops the display from auto-dimming while the device is connected to a charger.")),
    _t(TweakID.SBHideLowPowerAlerts, Section.SPRINGBOARD, "Disable Low Battery Alerts",
       FileLocation.springboard, "SBHideLowPowerAlerts",
       description=QT_TRANSLATE_NOOP("Nugget", "Suppresses the 'Low Battery — 20% / 10%' system alerts.")),
    _t(TweakID.SBHideACPower, Section.SPRINGBOARD, "Hide AC Power on Lock Screen",
       FileLocation.springboard, "SBHideACPower",
       description=QT_TRANSLATE_NOOP("Nugget", "Hides the charging status from the Lock Screen while the device is plugged into AC power.")),
    _t(TweakID.SBNeverBreadcrumb, Section.SPRINGBOARD, "Disable Breadcrumbs",
       FileLocation.springboard, "SBNeverBreadcrumb",
       description=QT_TRANSLATE_NOOP("Nugget", "Disables the 'Return to <App>' breadcrumb button that appears in the status bar after opening a link from another app.")),
    _t(TweakID.SBShowSupervisionTextOnLockScreen, Section.SPRINGBOARD, "Show Supervision Text on Lock Screen",
       FileLocation.springboard, "SBShowSupervisionTextOnLockScreen",
       description=QT_TRANSLATE_NOOP("Nugget", "Shows the device-supervision text on the Lock Screen, like the '<Device> is supervised by <org>' label seen on MDM-managed devices.")),
    _t(TweakID.AirplaySupport, Section.SPRINGBOARD, "Enable AirPlay support for Stage Manager",
       FileLocation.springboard, "SBExtendedDisplayOverrideSupportForAirPlayAndDontFileRadars",
       description=QT_TRANSLATE_NOOP("Nugget", "Adds extended-display AirPlay support for Stage Manager so apps and external displays can use the feature more broadly.")),
    _t(TweakID.SBAlwaysShowSystemApertureInSnapshots, Section.SPRINGBOARD, "Show Dynamic Island in Screenshots",
       FileLocation.springboard, "SBAlwaysShowSystemApertureInSnapshots", min_version="17.4", iphone_only=True,
       description=QT_TRANSLATE_NOOP("Nugget", "Forces the Dynamic Island to appear in screenshots instead of being hidden or shrunk while the screenshot is taken.")),
    _t(TweakID.HideDICompletely, Section.SPRINGBOARD, "Hide Dynamic Island Completely",
       FileLocation.springboard, "SBSuppressDynamicIslandCompletely", min_version="17.4", iphone_only=True,
       description=QT_TRANSLATE_NOOP("Nugget", "Suppresses the Dynamic Island cutout completely so it is never drawn. Can make the screen look odd on devices with a pill cutout.")),
    _t(TweakID.SBShowAuthenticationEngineeringUI, Section.SPRINGBOARD, "Show Red/Green Authentication Line on Lock Screen",
       FileLocation.springboard, "SBShowAuthenticationEngineeringUI",
       description=QT_TRANSLATE_NOOP("Nugget", "Shows a red/green authentication progress indicator on the Lock Screen while Face ID or passcode checks are running (engineering debug UI).")),
    # DEAD 2026-10-01 (binary research): Apple removed the floating tab bar
    # (and this preference) in iPadOS 26.4 — the key is a stale no-op on
    # 26.6.1. Kept in the enum for history; never loaded, never applied,
    # never rendered.
    _t(TweakID.UseFloatingTabBar, Section.SPRINGBOARD, "Disable Floating Tab Bar",
       FileLocation.uikit, "UseFloatingTabBar", value=False, ipad_only=True, disabled=True,
       description=QT_TRANSLATE_NOOP("Nugget", "Uses the old fixed tab bar style instead of the floating tab bar on iPad. Enabled when the switch is OFF.")),
    _t(TweakID.SBDisableIconParallax, Section.SPRINGBOARD, "Disable Icon Parallax",
       FileLocation.springboard, "SBDisableParallax",
       description=QT_TRANSLATE_NOOP("Nugget", "Stops Home Screen icons from shifting with the device tilt (the parallax effect). Pair with Disable Icon Page-Control Parallax for a fully static Home Screen.")),
    # Hide Search Button: v4 placement (SpringBoard section) and v4 spec,
    # restored verbatim with the Liquid Glass set. Same writer as before:
    # managed SpringBoard location, key SBHomeScreenShowsSearchAffordance,
    # value False; the retired HideSearchAffordance name still aliases here.
    _t(TweakID.SBHideSearchAffordance, Section.SPRINGBOARD, "Hide Search Button on Home Screen",
       FileLocation.springboard, "SBHomeScreenShowsSearchAffordance", value=False,
       description=QT_TRANSLATE_NOOP("Nugget", "Removes the search button below the icons on the Home Screen (the faint search bar/icon above the Dock). Enabled when the switch is ON.")),


    # --- Internal Options ---
    _t(TweakID.SBBuildNumber, Section.INTERNAL, "Show Build Version in Status Bar", GP, "UIStatusBarShowBuildVersion",
       description=QT_TRANSLATE_NOOP("Nugget", "Displays the iOS build number (e.g. 21A5284a) in the status bar next to the iOS version.")),
    _t(TweakID.RTL, Section.INTERNAL, "Force Right-to-Left Layout", GP, "NSForceRightToLeftWritingDirection",
       description=QT_TRANSLATE_NOOP("Nugget", "Forces a right-to-left layout for the entire system, mirroring the UI as if your primary language were RTL."),
       excludes=(TweakID.LTR,)),
    _t(TweakID.LTR, Section.INTERNAL, "Force Left-to-Right Layout", GP, "NSForceLeftToRightWritingDirection",
       description=QT_TRANSLATE_NOOP("Nugget", "Forces a left-to-right layout across the whole system regardless of the RTL language setting."),
       excludes=(TweakID.RTL,)),
    # Disable thermal monitoring (launchd daemon kill switch). Source
    # structure (NOT copied code): leminlimez/Nugget
    # src/tweaks/daemons_tweak.py — Daemon.thermalmonitord =
    # ["com.apple.thermalmonitord"], presented on the Daemons page as
    # "Disable thermalmonitord". WorkSlop 5-layer audit vs iOS 26.6.1:
    #   key    "com.apple.thermalmonitord" (the launchd service label)
    #   path   /var/db/com.apple.xpc.launchd/disabled.plist (same file
    #          the shipped Daemons feature writes)
    #   value  true (bool)
    #   reader launchd's stock disabled.plist mechanism — the delivery
    #          channel is proven; the on-device effect is user-reported
    #          working (2026-10-03), not lab-verified here.
    # It shares the disabled.plist payload with the Daemons tweak; the
    # apply pass merges both into one dict (see AdvancedPlistTweak merge).
    _t(TweakID.DisableThermal, Section.INTERNAL, "Disable Thermal",
       FileLocation.disabledDaemons, "com.apple.thermalmonitord",
       description=QT_TRANSLATE_NOOP("Nugget", "Disables the thermalmonitord daemon via launchd's disabled list, so iOS stops applying thermal throttling. Reported working by users; also removes the device's thermal protection — the phone can run hotter under load. Re-enable by turning this off and applying again. A reboot is required.")),

    _t(TweakID.SBIconVisibility, Section.INTERNAL, "Show Hidden Icons on Home Screen", GP, "SBIconVisibility",
       description=QT_TRANSLATE_NOOP("Nugget", "Reveals hidden or disabled Home Screen icons, including internal placeholder icons that are normally not drawn.")),
    _t(TweakID.iMessageDiagnosticsEnabled, Section.INTERNAL, "iMessage Debugging", GP, "iMessageDiagnosticsEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables the iMessage engineering debug menu / diagnostics inside the Messages app.")),
    _t(TweakID.IDSDiagnosticsEnabled, Section.INTERNAL, "Continuity Debugging", GP, "IDSDiagnosticsEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables the Continuity engineering debug diagnostics in Settings (Apple ID and related sections).")),
    _t(TweakID.VCDiagnosticsEnabled, Section.INTERNAL, "FaceTime Debugging", GP, "VCDiagnosticsEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables FaceTime / VoIP engineering debug diagnostics.")),
    _t(TweakID.AccessoryDeveloperEnabled, Section.INTERNAL, "Show Accessory Developer Settings", GP, "AccessoryDeveloperEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Adds a hidden Accessory Developer settings page to the Settings app for testing accessories.")),
    # (ported from leminlimez/Nugget's load_internal(): BasicPlistTweak(FileLocation.globalPreferences, "GesturesEnabled"))
    _t(TweakID.KeyFlick, Section.INTERNAL, "Keyboard Key Flicks", GP, "GesturesEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables the iPad-style keyboard keyflicks on iPhones.")),
    _t(TweakID.DisableSecondsHand, Section.INTERNAL, "Disable Clock Icon Seconds Hand", GP, "SBDisableClockIconSecondsHand",
       description=QT_TRANSLATE_NOOP("Nugget", "Stops the animated second hand on the Clock app's Home Screen icon.")),
    _t(TweakID.ShowButtonHints, Section.INTERNAL, "Show Hardware Button Hints in Screenshots", GP, "SBHardwareButtonHintDropletsAlwaysVisibleInSnapshots",
       description=QT_TRANSLATE_NOOP("Nugget", "Shows the side button / action button hint labels in screenshots (engineering debug UI).")),
    _t(TweakID.AppStoreDebug, Section.INTERNAL, "App Store Debug Gesture", FileLocation.appStore, "debugGestureEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Enables the hidden debug gesture in the App Store app, used to dump store data and inspect the store backend.")),
    _t(TweakID.NotesDebugMode, Section.INTERNAL, "Notes Debug Mode", FileLocation.notes, "DebugModeEnabled",
       description=QT_TRANSLATE_NOOP("Nugget", "Turns on the Notes app debug menu for engineering debugging.")),
    _t(TweakID.BKDigitizerVisualizeTouches, Section.INTERNAL, "Show Touches With Debug Info", FileLocation.backboardd, "BKDigitizerVisualizeTouches",
       description=QT_TRANSLATE_NOOP("Nugget", "Visually marks every touch point on the screen with debugging information as you touch. Great for diagnosing touch issues.")),
    _t(TweakID.BKHideAppleLogoOnLaunch, Section.INTERNAL, "Hide Respring Icon", FileLocation.backboardd, "BKHideAppleLogoOnLaunch",
       description=QT_TRANSLATE_NOOP("Nugget", "Hides the Apple logo animation during respring, showing a black screen instead until the UI comes back.")),
    _t(TweakID.EnableWakeGestureHaptic, Section.INTERNAL, "Vibrate on Raise-to-Wake", FileLocation.coreMotion, "EnableWakeGestureHaptic",
       description=QT_TRANSLATE_NOOP("Nugget", "Plays a Taptic Engine vibration when the device wakes via the raise-to-wake gesture.")),
    _t(TweakID.PlaySoundOnPaste, Section.INTERNAL, "Play Sound on Paste", FileLocation.pasteboard, "PlaySoundOnPaste",
       description=QT_TRANSLATE_NOOP("Nugget", "Plays a sound every time content is pasted anywhere on the device.")),
    _t(TweakID.AnnounceAllPastes, Section.INTERNAL, "Show Notifications for System Pastes", FileLocation.pasteboard, "AnnounceAllPastes",
       description=QT_TRANSLATE_NOOP("Nugget", "Shows a system notification whenever an app reads the pasteboard, acting as a privacy indicator for system-level pastes.")),
    # === Liquid Glass — WorkSlop v4 set restored VERBATIM (user order
    # 2026-10-03: re-implement the v4 Liquid Glass code unchanged). Every
    # spec below is byte-identical to v4 (src/tweaks/registry.py @
    # 4f44415): same key, file location, value/type, and version gates.
    # The Wave 10 replacement candidates and their UNPROVEN/device-test
    # labelling are gone. Proof: tools/test_wave11_lg_v4_verbatim.py.
    # === Partial Liquid Glass disable batch (2026-10-17, lg-partial-26) ===
    # Binary-attested keys from the iOS 26.1 dyld (audit:
    # ~/workspace/riset/audit-kandidat-lg-26.md). K1/K3/K4/K5/K6 are
    # verified-structure; the last two are structural-hypothesis.
    # Device-proven NOT required per user 2026-10-17 — honest grade in
    # each description instead. All write GP via partial restore.
    _t(TweakID.DisallowGlassLockScreen, Section.LIQUID_GLASS, "Disallow Glass on Lock Screen",
       GP, "SBDisallowGlassLockScreen",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disallow Liquid Glass on the Lock Screen (verified-structure: key found in SpringBoardFoundation binary). The direct answer to glass reflections during the Home Screen to Lock Screen transition. Unverified on device — needs device test.")),
    _t(TweakID.DisableHSGlassExterior, Section.LIQUID_GLASS, "Disable Home Screen Glass Exterior",
       GP, "SolariumEnableHomeScreenExteriorEffects", value=False,
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Turns off the exterior glass effects (reflections/specular highlights) on the Home Screen (verified-structure: DesignLibrary binary pattern SolariumEnable<Area>ExteriorEffects). Enabled when the switch is ON. Unverified on device — needs device test.")),
    _t(TweakID.DisableDockGlassExterior, Section.LIQUID_GLASS, "Disable Dock Glass Exterior",
       GP, "SolariumEnableDockExteriorEffects", value=False,
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Turns off the exterior glass effects (reflections/specular highlights) on the Dock (verified-structure). Enabled when the switch is ON. Unverified on device — needs device test.")),
    _t(TweakID.DisableKeyboardGlassExterior, Section.LIQUID_GLASS, "Disable Keyboard Glass Exterior",
       GP, "SolariumEnableKeyboardExteriorEffects", value=False,
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Turns off the exterior glass effects on the keyboard, making it look like the flat iOS 18 keyboard (verified-structure: DesignLibrary binary). Enabled when the switch is ON. Unverified on device — needs device test.")),
    _t(TweakID.DisableSolariumFocusForeground, Section.LIQUID_GLASS, "Disable Solarium Focus Foreground Effects",
       GP, "SolariumDisableFocusForegroundEffects",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disables the Solarium foreground effects shown while focusing (verified-structure). Unverified on device — needs device test.")),
    _t(TweakID.SolariumForceDarkShadow, Section.LIQUID_GLASS, "Force Dark Glass Shadow",
       GP, "SolariumForceDarkShadow",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Forces dark shadows on Liquid Glass surfaces (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    _t(TweakID.SolariumHighlightWhite, Section.LIQUID_GLASS, "White Glass Highlight",
       GP, "SolariumHighlightWhite",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "White highlight on Liquid Glass surfaces (structural-hypothesis: binary-attested key). Unverified — needs device test.")),
    # K8 (deep-audit PROMOTE 2026-10-17): Solarium pref-family keys, each
    # binary-attested exactly once in the DesignLibrary string table alongside
    # confirmed GP prefs (SolariumNoBlurReducedFrost, SolariumIncreasedDiffusion).
    # Reader not confirmed by disassembly (FUSE/APFS blocked in this VM) —
    # structural-hypothesis grade, device test required.
    _t(TweakID.SolariumBackgroundFilter, Section.LIQUID_GLASS, "Solarium Background Filter",
       GP, "SolariumBackgroundFilter",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Toggles the Solarium background filter stage (structural-hypothesis: binary-attested Solarium-family key). Unverified — needs device test.")),
    _t(TweakID.SolariumTextFrost, Section.LIQUID_GLASS, "Solarium Text Frost",
       GP, "SolariumTextFrost",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Toggles the frost effect applied to text on Liquid Glass surfaces (structural-hypothesis: binary-attested Solarium-family key). Unverified — needs device test.")),
    _t(TweakID.SolariumUseDisplayAngle, Section.LIQUID_GLASS, "Solarium Use Display Angle",
       GP, "SolariumUseDisplayAngle",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Makes Solarium lighting react to the display viewing angle (structural-hypothesis: binary-attested Solarium-family key). Unverified — needs device test.")),
    _t(TweakID.SolariumForceFallback, Section.LIQUID_GLASS, "Force Solarium Fallback", GP, "SolariumForceFallback",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Force iOS to use Liquid Glass fallback mode. Unverified — needs device test.")),
    _t(TweakID.DisableSolariumSwiftUI, Section.LIQUID_GLASS, "Disable Solarium (SwiftUI)", GP, "com.apple.SwiftUI.DisableSolarium",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable Solarium for SwiftUI. Reader removed in 26.1 — likely non-functional.")),
    _t(TweakID.GlassLegibility2, Section.LIQUID_GLASS, "Glass Legibility Value 2", FileLocation.uikit, "UIViewGlassLegibilitySetting", value=2,
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Glass legibility value 2 = unobserved branch. 0=Clear, 1=Tinted (proven).")),
    _t(TweakID.SolariumFeatureFlags, Section.FEATURE_FLAGS, "Solarium Feature Flags", FileLocation.featureflags, "SolariumFlags",
       min_version="26.0", max_version="26.1", description=QT_TRANSLATE_NOOP("Nugget", "PLACEHOLDER: Specific Solarium flags not yet defined. Channel dead on 26.2+. WARNING: Can break Control Center.")),
    _t(TweakID.DisallowGlassTime, Section.LIQUID_GLASS, "Disallow Glass on LS Clock", GP, "SBDisallowGlassTime",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disallow glass effect on Lock Screen clock.")),
    _t(TweakID.DisableGlassDock, Section.LIQUID_GLASS, "Disable Glass on Dock", GP, "SBDisableGlassDock",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable Liquid Glass on Dock — solid style.")),
    _t(TweakID.FlatIconsEverywhere, Section.LIQUID_GLASS, "Flat Icons Everywhere", GP, "SBUseFlatIconsEverywhere",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Force all icons flat, no 3D/glass effect.")),
    _t(TweakID.DisableWidgetSpecular, Section.LIQUID_GLASS, "Disable Widget Specular", GP, "SBDisableWidgetSpecular",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove specular highlight from widgets.")),
    _t(TweakID.DisableDockSpecular, Section.LIQUID_GLASS, "Disable Dock Specular", GP, "SBDisableDockSpecular",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove specular highlight from dock.")),
    _t(TweakID.DisableFolderSpecular, Section.LIQUID_GLASS, "Disable Folder Specular", GP, "SBDisableFolderSpecular",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove specular highlight from folders.")),
    _t(TweakID.ExcludeClearGlassShadows, Section.LIQUID_GLASS, "Exclude Clear Glass Shadows", GP, "SBExcludeAllClearGlassShadows",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove all Clear Glass shadows.")),
    _t(TweakID.ExcludeDockShadow, Section.LIQUID_GLASS, "Exclude Dock Shadow", GP, "SBExcludeDockShadow",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove dock drop shadow.")),
    _t(TweakID.ExcludeSearchShadow, Section.LIQUID_GLASS, "Exclude Search Shadow", GP, "SBExcludeSearchShadow",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove search field shadow.")),
    _t(TweakID.DisableOuterRefraction, Section.LIQUID_GLASS, "Disable Outer Refraction", GP, "SolariumDisableOuterRefraction",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable liquid bending at glass edges.")),
    _t(TweakID.DisableSolariumHDR, Section.LIQUID_GLASS, "Disable Solarium HDR", GP, "SolariumAllowHDR", value=False,
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable HDR tone-mapping. Value=False.")),
    _t(TweakID.DisableSpecularMotion, Section.LIQUID_GLASS, "Disable Specular Motion", GP, "SBDisableSpecularEverywhereUsingLSSAssertion",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable motion-based specular.")),
    _t(TweakID.DisableSpecularEverywhere, Section.LIQUID_GLASS, "Disable Specular Everywhere", GP, "SBDisableSpecularEverywhere",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove specular from all CC tiles.")),
    _t(TweakID.DisableGlassEverywhere, Section.LIQUID_GLASS, "Disable Glass Everywhere (Predicted)", GP, "SBDisableGlassEverywhere",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Predicted key — pattern hypothesis.")),
    _t(TweakID.DisallowGlassEverywhere, Section.LIQUID_GLASS, "Disallow Glass Everywhere (Predicted)", GP, "SBDisallowGlassEverywhere",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Predicted key — pattern hypothesis.")),
    _t(TweakID.DisableLockScreenSpecular, Section.LIQUID_GLASS, "Disable LS Specular (Predicted)", GP, "SBDisableLockScreenSpecular",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove specular from Lock Screen. Predicted.")),
    _t(TweakID.DisableClockSpecular, Section.LIQUID_GLASS, "Disable Clock Specular (Predicted)", GP, "SBDisableClockSpecular",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove specular from LS clock. Predicted.")),
    _t(TweakID.DisableGlassLockScreen, Section.LIQUID_GLASS, "Disable Glass on LS (Predicted)", GP, "SBDisableGlassLockScreen",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable glass on Lock Screen. Predicted.")),
    _t(TweakID.DisableCompactChrome, Section.LIQUID_GLASS, "Disable Compact Chrome", GP, "DisableSolariumCompactChrome",
       min_version="27.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable Solarium compact chrome. Gate 27.0.")),
    _t(TweakID.DisableGlassDI, Section.LIQUID_GLASS, "Disable Glass on DI (Predicted)", GP, "SBDisableGlassDynamicIsland",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable glass on Dynamic Island. Predicted.")),
    _t(TweakID.DisallowGlassDI, Section.LIQUID_GLASS, "Disallow Glass on DI (Predicted)", GP, "SBDisallowGlassDynamicIsland",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disallow glass on DI. Predicted.")),
    _t(TweakID.DisableIslandSpecular, Section.LIQUID_GLASS, "Disable Island Specular (Predicted)", GP, "SBDisableIslandSpecular",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove DI specular. Predicted.")),
    _t(TweakID.ExcludeAllGlassShadows, Section.LIQUID_GLASS, "Exclude All Glass Shadows (Predicted)", GP, "SBExcludeAllGlassShadows",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Remove all glass shadows. Predicted.")),
    _t(TweakID.FlatDockEverywhere, Section.LIQUID_GLASS, "Flat Dock Everywhere (Predicted)", GP, "SBUseFlatDockEverywhere",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Flat dock everywhere. Predicted.")),
    _t(TweakID.DisableGlassBlur, Section.LIQUID_GLASS, "Disable Glass Blur (Predicted)", GP, "SBDisableGlassBlur",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable glass blur. Predicted.")),
    _t(TweakID.DisallowGlassKeyboard, Section.LIQUID_GLASS, "Disallow Glass Keyboard (Predicted)", GP, "SBDisallowGlassKeyboard",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disallow keyboard glass. Predicted.")),
    _t(TweakID.DisableRefractionEverywhere, Section.LIQUID_GLASS, "Disable Refraction Everywhere (Predicted)", GP, "SBDisableRefractionEverywhere",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Disable refraction everywhere. Predicted.")),
    _t(TweakID.LGLPMGestalt, Section.LIQUID_GLASS, "LG Low Power Mode Signal", FileLocation.mga, "SAGvsp6O6kAQ4fEfDJpC4Q",
       min_version="26.0", max_version="26.1", description=QT_TRANSLATE_NOOP("Nugget", "LGLPM MobileGestalt signal. BLOCKED on iOS 26.2+ (Apple locked MobileGestalt).")),
    # Blurr Motion (2026-10-03, dossier candidate B-1 — NOT part of the
    # v4 set; see tools/test_wave11_blurr_motion.py).
    _t(TweakID.BlurrMotion, Section.LIQUID_GLASS, "Blurr Motion", GP, "SolariumIncreasedDiffusion",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Research candidate for thicker frost blur on Liquid Glass surfaces: its key was found in the DesignLibrary material cluster in the iOS 23G83 binary, but the effect on a real device is not proven yet. Back up fully first, turn Low Power Mode OFF, apply it on its own, reboot, then judge each surface on its own (Dock, Control Center, notifications, folders, App Switcher, Lock Screen clock). Turning it off and applying again removes the key.")),
    # === Non-glass candidates (audited) ===
    _t(TweakID.CustomLockDate, Section.SPRINGBOARD, "Custom Lock Screen Date", FileLocation.globalPreferencesHomeDomain, "AppleICUDateTimeSymbols",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Custom Lock Screen date format. Device-proven (iOS 26.0-26.7).")),
    _t(TweakID.AnimDragCoeff, Section.SPRINGBOARD, "Animation Speed Coefficient", GP, "UIAnimationDragCoefficient", value=0.5,
       min_version="26.0", kind=Kind.NUMBER, min_value=0, max_value=5, step=0.1,
       description=QT_TRANSLATE_NOOP("Nugget", "Animation speed: <1 faster, >1 slower, 0 disables.")),
    # === Remaining audited candidates ===
    # REMOVED (Wave 10, user order 2026-10-02): the predicted Liquid Glass
    # entries that used to sit around DisableCompactChrome —
    # DisableLockScreenSpecular, DisableClockSpecular,
    # DisableGlassLockScreen, DisableGlassDI, DisallowGlassDI,
    # DisableIslandSpecular, ExcludeAllGlassShadows, FlatDockEverywhere,
    # DisableGlassBlur, DisallowGlassKeyboard, and
    # DisableRefractionEverywhere — are deleted from the v10 product
    # registry. TweakID tombstones remain in REMOVED_TWEAK_IDS only.
    # === Remaining: status bar, notifications, keyboard, siri ===
    # REMOVED: StatusBarOverrides was incorrectly registered as a plist key.
    # The actual statusBarOverrides is a BINARY STRUCT file at
    # /var/mobile/Library/SpringBoard/statusBarOverrides (iOS 26), not a plist.
    # It requires manual binary file creation, not BasicPlistTweak.
    # See ~/workspace/riset/ for the visual signal research.
    _t(TweakID.ShowSystemServices, Section.SPRINGBOARD, "Show System Services Icons", GP, "ShowSystemServices",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Show/hide VPN/Location/Alarm icons.")),
    # === WorkSlop own system — remaining audited candidates (not GoldenNugget copy) ===
    # REMOVED: GranularSpringBoard used invented key SBGranularGlass (not a real
    # Apple key). The granular controls are N1-N7 (SBUseFlatIconsEverywhere, etc.)
    # which are implemented as separate entries below.
    # REMOVED (Wave 10): LGLPMGestalt was registered here as a BasicPlistTweak
    # writing the MobileGestalt key SAGvsp6O6kAQ4fEfDJpC4Q as a top-level key
    # into FileLocation.mga. That delivery model is wrong — MobileGestalt
    # tweaks patch CacheExtra in the device's own plist. The registry model
    # is deleted; old presets naming LGLPMGestalt resolve to removed/skipped
    # via src/tweaks/capabilities.py::REMOVED_TWEAK_IDS, never applied. No
    # registry spec may target FileLocation.mga without a MobileGestalt
    # factory.
    # REMOVED (Wave 10 Package 1, audit kill list): the Settings-duplicate
    # SpringBoard/Keyboard/Siri rows, the ten wrong-domain Notification
    # rows, the wrong value/type rows (DisableSearchingWebsites,
    # SiriTriggerPhrase, SiriVocab), the dead-reader Liquid Glass
    # specular/shadow/refraction/HDR rows plus DisableCompactChrome, and
    # the five redundant duplicate rows (SuppressDICompletely,
    # DisableParallax, HideSearchAffordance, IconVisibility,
    # DisableClockSeconds) are deleted from the active v10 registry.
    # Non-duplicate kills stay tombstoned in REMOVED_TWEAK_IDS; the five
    # duplicate names alias to their canonical IDs there.
    _t(TweakID.KbGestureIntro, Section.INTERNAL, "Keyboard Gesture Intro", GP, "DidShowGestureKeyboardIntroduction",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Re-show gesture keyboard introduction.")),
    _t(TweakID.KbAutoLists, Section.INTERNAL, "Keyboard Autocorrect Lists", GP, "KeyboardAutocorrectionLists",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Android-style autocorrect bar.")),
    _t(TweakID.SiriSpeakerTTS, Section.INTERNAL, "Speaker for TTS", GP, "Use device speaker for TTS",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Route Siri voice through device speaker.")),
    _t(TweakID.SiriDeclined, Section.INTERNAL, "Siri Declined Flag", GP, "UserHasDeclinedEnable",
       min_version="26.0", description=QT_TRANSLATE_NOOP("Nugget", "Flag for declined Siri setup.")),
) + _FF_SPECS

SPECS_BY_SECTION = {section: [s for s in SPECS if s.section == section and not s.disabled] for section in Section}
SPECS_BY_ID = {spec.id: spec for spec in SPECS if not spec.disabled}


def home_tweak_catalogue(specs_by_section=None) -> tuple:
    """Registry-derived Home catalogue entries for every active spec.

    Home consumes this instead of a hand-maintained tweak list, so adding
    one registry spec surfaces it on Home automatically. ``specs_by_section``
    is injectable for tests; by default the live ``SPECS_BY_SECTION``
    mapping is read at call time so a registry rebuild is reflected without
    editing Home. Removed tombstones and retired duplicate aliases are not
    specs and therefore never appear as separate Home entries.
    """
    source = SPECS_BY_SECTION if specs_by_section is None else specs_by_section
    entries = []
    for section in Section:
        feature = SECTION_FEATURES.get(section, section.value)
        for spec in source.get(section, []):
            if getattr(spec, "disabled", False):
                continue
            entries.append({
                "id": spec.id,
                "id_name": spec.id.name,
                "title": spec.title,
                "section": section,
                "section_name": section.value,
                "feature": feature,
                "location": spec.location,
                "location_path": spec.location.value,
                "key": spec.key,
            })
    return tuple(entries)
