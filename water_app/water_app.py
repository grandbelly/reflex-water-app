"""
Water Quality Monitoring Application
Supports both RPI (lightweight) and CPS (full-featured) versions via Feature Flags

VERSION_TYPE environment variable controls which features are enabled:
- RPI: Dashboard, Trends, Alarms, Communications (4 menus)
- CPS: RPI features + AI Insights, SCADA Alarms (6 menus)
"""

import os
import reflex as rx
from reflex.utils import console

# Get version type from environment
VERSION_TYPE = os.getenv("VERSION_TYPE", "RPI").upper()  # Default to RPI

# Database and security
from .db import get_pool
from .security import validate_startup_security

# ============================================================================
# COMMON PAGES (RPI + CPS)
# ============================================================================
from .pages.common.dashboard import dashboard_page
from .pages.common.trends import trends_page
from .pages.common.alarms import alarms_page
from .pages.common.communications import communications_page

# ============================================================================
# COMMON STATES (RPI + CPS)
# ============================================================================
from .states.common.trend_state import TrendState
from .states.common.alarms_state import AlarmsState
from .states.common.communications_state import CommunicationState

# ============================================================================
# CPS-ONLY PAGES (Conditional Import)
# ============================================================================
if VERSION_TYPE == "CPS":
    from .pages.cps_only.ai_insights import ai_insights_page
    from .pages.cps_only.scada_alarm_comparison import scada_alarm_comparison

# ============================================================================
# CPS-ONLY STATES (Conditional Import)
# ============================================================================
if VERSION_TYPE == "CPS":
    from .states.cps_only.ai_state import AIState
    from .states.cps_only.scada_alarm_comparison_state import ScadaAlarmComparisonState

# ============================================================================
# APP CONFIGURATION
# ============================================================================
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
    ),
)

# ============================================================================
# STARTUP INITIALIZATION
# ============================================================================
@app.on_load
async def on_app_load():
    """Application startup: security validation and database pool initialization"""
    console.log(f"🚀 Water App starting... (VERSION: {VERSION_TYPE})")

    # Security validation
    if not validate_startup_security():
        console.error("❌ Security validation failed!")
        raise RuntimeError("Security validation failed")

    console.log("✅ Security validation passed")
    console.log("🔌 Initializing database connection pool...")

    # Initialize connection pool
    pool = await get_pool()
    console.log(f"✅ Connection pool initialized (max={pool.max_size})")

    # Log enabled features
    if VERSION_TYPE == "CPS":
        console.log("🤖 CPS Mode: AI Insights & SCADA Alarms enabled")
    else:
        console.log("📊 RPI Mode: Core monitoring features only")

# ============================================================================
# PAGE REGISTRATION - COMMON (4 menus, always available)
# ============================================================================
app.add_page(
    dashboard_page,
    route="/",
    title="Dashboard - Water Monitor",
    on_load=[]
)

app.add_page(
    trends_page,
    route="/trends",
    title="Trends - Water Monitor",
    on_load=TrendState.load_initial_data
)

app.add_page(
    alarms_page,
    route="/alarms",
    title="Alarms - Water Monitor",
    on_load=AlarmState.load_initial_data
)

app.add_page(
    communications_page,
    route="/comm",
    title="Communications - Water Monitor",
    on_load=CommunicationState.load_initial_data
)

# ============================================================================
# PAGE REGISTRATION - CPS ONLY (2 menus, conditional)
# ============================================================================
if VERSION_TYPE == "CPS":
    app.add_page(
        ai_insights_page,
        route="/ai",
        title="AI Insights - Water Monitor",
        on_load=AIState.load_initial_sensor_data
    )

    app.add_page(
        scada_alarm_comparison,
        route="/scada",
        title="SCADA Alarms - Water Monitor",
        on_load=ScadaAlarmComparisonState.load_alarms
    )

    console.log("✅ Water App: 6 pages registered (RPI + CPS)")
    console.log("📊 Dashboard, Trends, Alarms, Communications")
    console.log("🤖 AI Insights, SCADA Alarms")
else:
    console.log("✅ Water App: 4 pages registered (RPI only)")
    console.log("📊 Dashboard, Trends, Alarms, Communications")
