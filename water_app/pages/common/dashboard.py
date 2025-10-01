"""Unified Dashboard Page - MVC + Real-time Pattern"""
import reflex as rx
from water_app.views.dashboard_realtime_view import dashboard_realtime_page
from water_app.states.common.dashboard_realtime import DashboardRealtimeState
from water_app.components.layout import shell


def dashboard_page() -> rx.Component:
    """Main dashboard with real-time updates using MVC pattern"""
    return shell(
        dashboard_realtime_page(),
        active_route="/",
        on_mount=DashboardRealtimeState.start_streaming
    )