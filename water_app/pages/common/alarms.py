"""
Alarms Page - Unified rule-based alarm monitoring
- Clean, simple UI
- RULE_BASE scenario alarms
- Uses service pattern
"""
import reflex as rx
from typing import Dict
from water_app.states.common.alarms import AlarmsState
from water_appcomponents.layout import shell


def level_badge(level: int, level_name: str) -> rx.Component:
    """Badge for alarm level with color"""
    color_map = {
        5: "red",     # CRITICAL
        4: "orange",  # ERROR
        3: "yellow",  # WARNING
        2: "blue",    # INFO
        1: "gray",    # CAUTION
    }

    color = color_map.get(level, "gray")

    return rx.badge(
        level_name,
        color_scheme=color,
        variant="solid",
    )


def stat_tile(title: str, value: rx.Var, color: str = "blue") -> rx.Component:
    """Statistics tile"""
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", color="gray"),
            rx.text(value, size="6", weight="bold"),
            spacing="1",
            align="center",
        ),
        padding="4",
        border_radius="lg",
        bg=rx.color(color, 2),
        width="100%",
    )


def alarm_card(alarm: Dict) -> rx.Component:
    """Alarm card component"""
    return rx.box(
        rx.vstack(
            # Header: Level badge + Time
            rx.hstack(
                level_badge(alarm["level"], alarm["level_name"]),
                rx.spacer(),
                rx.text(
                    alarm["triggered_at_short"],
                    size="2",
                    color="gray"
                ),
                width="100%",
            ),

            # Message
            rx.text(
                alarm["message"],
                size="3",
                weight="medium",
            ),

            # Sensor info
            rx.hstack(
                rx.badge(alarm["tag_name"], variant="soft", color_scheme="blue"),
                rx.text(f"{alarm['value']}{alarm['unit']}", size="2", color="gray"),
                rx.cond(
                    alarm["acknowledged"],
                    rx.badge("✓ Acknowledged", variant="soft", color_scheme="green"),
                    rx.button(
                        "Acknowledge",
                        size="1",
                        variant="soft",
                        on_click=lambda: AlarmsState.acknowledge_alarm(alarm["event_id"]),
                    ),
                ),
                spacing="2",
            ),

            spacing="2",
            align="start",
            width="100%",
        ),
        padding="4",
        border=f"1px solid {rx.color('gray', 3)}",
        border_radius="lg",
        width="100%",
        _hover={"bg": rx.color("gray", 1)},
    )


def alarms_page() -> rx.Component:
    """Main alarms page"""
    return shell(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("🚨 Alarms", size="6"),
                rx.spacer(),
                rx.button(
                    "↻ Refresh",
                    on_click=AlarmsState.refresh_data,
                    loading=AlarmsState.loading,
                ),
                width="100%",
            ),

            # Statistics
            rx.hstack(
                stat_tile("Total", AlarmsState.statistics["total"], "gray"),
                stat_tile("Critical", AlarmsState.statistics["critical"], "red"),
                stat_tile("Warning", AlarmsState.statistics["warning"], "yellow"),
                stat_tile("Info", AlarmsState.statistics["info"], "blue"),
                stat_tile("Unacknowledged", AlarmsState.statistics["unacknowledged"], "orange"),
                spacing="3",
                width="100%",
            ),

            # Filters
            rx.hstack(
                rx.text("Time Range:", size="2", weight="medium"),
                rx.segmented_control.root(
                    rx.segmented_control.item("1h", value="1"),
                    rx.segmented_control.item("6h", value="6"),
                    rx.segmented_control.item("24h", value="24"),
                    rx.segmented_control.item("7d", value="168"),
                    default_value="168",  # Changed from "24" to "168" (7 days)
                    on_change=AlarmsState.set_hours_filter,
                ),
                rx.spacer(),
                rx.switch(
                    "Show Acknowledged",
                    checked=AlarmsState.show_acknowledged,
                    on_change=AlarmsState.toggle_show_acknowledged,
                ),
                width="100%",
                align="center",
            ),

            # Last Update
            rx.text(
                f"Last update: {AlarmsState.last_update}",
                size="1",
                color="gray",
            ),

            # Error message
            rx.cond(
                AlarmsState.error_message != "",
                rx.callout(
                    AlarmsState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                ),
                rx.box(),
            ),

            # Alarm List
            rx.cond(
                AlarmsState.loading,
                rx.center(
                    rx.spinner(size="3"),
                    padding="8",
                ),
                rx.cond(
                    AlarmsState.filtered_alarms.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            AlarmsState.filtered_alarms,
                            alarm_card,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.center(
                        rx.text("No alarms found", color="gray", size="3"),
                        padding="8",
                    ),
                ),
            ),

            spacing="4",
            width="100%",
            padding="4",
        ),
    )