# config.py — Central configuration for the Job Market Intelligence Dashboard

import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "db", "jobs.db")

# App Meta
APP_TITLE    = "Job Market Intelligence"
APP_ICON     = "📊"
APP_LAYOUT   = "wide"
SIDEBAR_STATE = "expanded"

# Color Palette (Plotly-compatible)
PRIMARY_COLOR   = "#6366F1"   # Indigo

# Discrete color sequence used across all charts
COLOR_SEQUENCE = [
    "#6366F1", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#06B6D4", "#EC4899", "#14B8A6",
    "#F97316", "#84CC16",
]

# Chart Defaults
CHART_HEIGHT       = 450
CHART_TEMPLATE     = "plotly_dark"   # or "plotly_white" / "plotly"


# Top-N defaults
TOP_N_DEFAULT = 15

# Experience levels order (for consistent axis ordering) 
EXP_LEVEL_ORDER = ["Entry Level", "Mid Level", "Senior Level", "Lead/Manager"]
