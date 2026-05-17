from __future__ import annotations

# ---------------------------------------------------------------------------
# Background hierarchy
# Neutral dark gray with subtle cool tint — avoids the "gaming" navy aesthetic.
# Each level is ~6-8 lightness points above the previous (WCAG-aware hierarchy).
# ---------------------------------------------------------------------------
BG_PRIMARY = "#111318"  # main window canvas
BG_SECONDARY = "#1a1d24"  # card / panel surface
BG_TERTIARY = "#222630"  # header, elevated surfaces, active sidebar items
BG_INPUT = "#2a2f3e"  # text inputs, scrollable areas
BG_HOVER = "#2f3446"  # hover state on interactive list items

# ---------------------------------------------------------------------------
# Borders and dividers
# Subtle borders give cards depth without color contrast noise.
# ---------------------------------------------------------------------------
BORDER_COLOR = "#2e3347"  # card and panel borders
DIVIDER_COLOR = "#252a37"  # thin horizontal / vertical separators

# ---------------------------------------------------------------------------
# Accent
# Red is the primary action color (approved in 12.1 architecture decision).
# Kept as-is; the neutral gray base makes it pop without looking aggressive.
# ---------------------------------------------------------------------------
ACCENT = "#e94560"
ACCENT_HOVER = "#c73652"
ACCENT_DISABLED = "#6b2535"

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
TEXT_PRIMARY = "#e8eaf0"  # body text on dark backgrounds
TEXT_SECONDARY = "#8b90a0"  # metadata, labels, secondary info
TEXT_DISABLED = "#4a4f62"  # placeholder, disabled controls
TEXT_MONO = "#a8b2c8"  # log / terminal text (slightly blue-tinted)

# ---------------------------------------------------------------------------
# Semantic state colors
# ---------------------------------------------------------------------------
COLOR_SUCCESS = "#4ade80"  # text / icon on success state
COLOR_ERROR = "#f87171"  # text / icon on error state
COLOR_WARNING = "#fbbf24"  # text / icon on warning state
COLOR_PROCESSING = "#60a5fa"  # text / icon on running state
COLOR_IDLE = "#6b7280"  # text / icon on idle state

# Badge backgrounds — semi-opaque tints, distinct from card bg
COLOR_SUCCESS_BG = "#14291e"
COLOR_ERROR_BG = "#2d1515"
COLOR_WARNING_BG = "#2d2010"
COLOR_PROCESSING_BG = "#162038"

# ---------------------------------------------------------------------------
# Log / terminal area
# Slightly darker than cards to visually separate as a "terminal" surface.
# ---------------------------------------------------------------------------
LOG_BG = "#0d0f14"
LOG_BORDER = "#1e2230"

# ---------------------------------------------------------------------------
# Fonts
# FONT_SECTION uses uppercase small — standard pattern in developer tools
# for panel/section labels (VS Code sidebar, Linear, etc.).
# ---------------------------------------------------------------------------
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SUBTITLE = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_SECTION = ("Segoe UI", 9, "bold")  # uppercase section labels
FONT_MONO = ("Consolas", 11)  # log viewer / terminal

# ---------------------------------------------------------------------------
# Spacing (px)
# ---------------------------------------------------------------------------
PAD_XS = 4
PAD_SM = 8
PAD_MD = 16
PAD_LG = 24
PAD_XL = 32

CORNER_RADIUS = 8
CORNER_RADIUS_BADGE = 20  # pill shape for status badges
BORDER_WIDTH = 1

# ---------------------------------------------------------------------------
# Window geometry
# ---------------------------------------------------------------------------
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1100
WINDOW_DEFAULT_HEIGHT = 680

# ---------------------------------------------------------------------------
# Component sizes
# ---------------------------------------------------------------------------
HEADER_HEIGHT = 52
LOG_PANEL_HEIGHT = 185
BUTTON_HEIGHT = 36
BUTTON_WIDTH_PRIMARY = 160
WORD_PANEL_WIDTH = 290
