"""Dashboard Real-time View - UI Components following stock market pattern"""
import reflex as rx
import reflex_chakra as rc
from typing import Dict, List
from water_app.states.dashboard_realtime import DashboardRealtimeState


def realtime_header() -> rx.Component:
    """Simplified header - no controls, always live"""
    return rx.box(
        rx.hstack(
            rx.spacer(),
            width="100%",
            align="center"
        ),
        padding="3",
        background="white",
        display="none"  # Hide the header completely since no controls needed
    )


def status_bar() -> rx.Component:
    """Status bar showing system health"""

    return rx.box(
        rx.hstack(
            rx.badge(
                rx.hstack(
                    rx.icon("circle", size=10, color="green.500", style={"animation": "pulse 2s infinite"}),
                    rx.text("LIVE", size="1", weight="bold"),
                    spacing="1"
                ),
                variant="soft",
                color_scheme="green",
                size="2",
                style={"border-radius": "9999px"}
            ),
            rx.text(
                f"Last update: {DashboardRealtimeState.last_update}",
                size="1",
                color="gray.600",
                style={"font-family": "monospace"}
            ),
            rx.spacer(),
            rx.hstack(
                rx.text("정상:", size="2", weight="medium", color="green.700"),
                rx.text(DashboardRealtimeState.normal_count, size="2", weight="bold", color="green.600"),
                rx.text("|", color="gray.400"),
                rx.text("주의:", size="2", weight="medium", color="yellow.700"),
                rx.text(DashboardRealtimeState.warning_count, size="2", weight="bold", color="yellow.600"),
                rx.text("|", color="gray.400"),
                rx.text("위험:", size="2", weight="medium", color="red.700"),
                rx.text(DashboardRealtimeState.critical_count, size="2", weight="bold", color="red.600"),
                spacing="2"
            ),
            width="100%",
            align="center"
        ),
        padding="3",
        background="linear-gradient(90deg, var(--gray-2), var(--gray-1))",
        border_radius="lg",
        border="1px solid",
        border_color="gray.200"
    )


def sensor_gauge(sensor_data: Dict) -> rx.Component:
    """Circular gauge component - using Chakra circular progress"""
    return rc.circular_progress(
        rc.circular_progress_label(
            f"{sensor_data['value']:.1f}",
            font_size="lg",
            font_weight="bold"
        ),
        value=sensor_data["gauge_percent"],
        size="80px",
        thickness="8px",
        color=rx.cond(
            sensor_data["status"] == 0,
            "green.400",
            rx.cond(
                sensor_data["status"] == 1,
                "yellow.400",
                "red.400"
            )
        ),
        track_color="gray.200"
    )


def mini_chart(data: List[Dict]) -> rx.Component:
    """Mini sparkline chart with tooltip"""
    return rx.recharts.area_chart(
        rx.recharts.area(
            data_key="value",
            stroke="currentColor",
            fill="currentColor",
            fill_opacity=0.2,
            stroke_width=2,
            dot=False
        ),
        rx.recharts.x_axis(data_key="timestamp", hide=True),
        rx.recharts.y_axis(hide=True),
        rx.recharts.tooltip(
            content_style={
                "backgroundColor": "rgba(255, 255, 255, 0.95)",
                "border": "1px solid #ccc",
                "borderRadius": "4px",
                "padding": "8px"
            },
            label_style={
                "color": "#333",
                "fontWeight": "bold",
                "marginBottom": "4px"
            },
            item_style={
                "color": "#666",
                "fontSize": "12px"
            }
        ),
        data=data,
        height=60,
        margin={"top": 5, "right": 5, "bottom": 5, "left": 5}
    )


def sensor_tile(sensor_data: Dict) -> rx.Component:
    """Individual sensor tile - like stock market ticker card"""
    return rx.card(
        rx.vstack(
            # Header with tag name
            rx.hstack(
                rx.text(
                    sensor_data["tag_name"],
                    font_weight="bold",
                    font_size="lg"
                ),
                rx.spacer(),
                rx.badge(
                    rx.cond(
                        sensor_data["status"] == 0,
                        "Normal",
                        rx.cond(
                            sensor_data["status"] == 1,
                            "Warning",
                            "Critical"
                        )
                    ),
                    color_scheme=rx.cond(
                        sensor_data["status"] == 0,
                        "green",
                        rx.cond(
                            sensor_data["status"] == 1,
                            "amber",
                            "red"
                        )
                    )
                ),
                width="100%"
            ),

            # Gauge and range info
            rx.hstack(
                sensor_gauge(sensor_data),
                rx.vstack(
                    rx.text(
                        f"Range: {sensor_data['min_val']:.0f}-{sensor_data['max_val']:.0f}",
                        font_size="xs",
                        color="gray.500"
                    ),
                    rx.text(
                        f"Current: {sensor_data['value']:.1f}",
                        font_size="sm",
                        color="gray.600"
                    ),
                    align_items="start",
                    spacing="1"
                ),
                spacing="4",
                align="center",
                width="100%"
            ),

            # Mini chart
            rx.box(
                mini_chart(sensor_data["chart_points"]),
                width="100%",
                height="60px",
                color=sensor_data["chart_color"]
            ),

            # Timestamp
            rx.text(
                sensor_data["timestamp"],
                font_size="xs",
                color="gray.500",
                text_align="center",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),
        padding="4",
        width="100%"
    )


def dashboard_realtime_page() -> rx.Component:
    """Main dashboard page - like stock market dashboard"""

    return rx.vstack(
        # Header
        realtime_header(),

        # Status bar
        status_bar(),

        # Sensor grid
        rx.grid(
            rx.foreach(
                DashboardRealtimeState.formatted_sensors,
                lambda sensor: sensor_tile(sensor)
            ),
            columns="4",
            spacing="4",
            width="100%"
        ),

        spacing="4",
        padding="4",
        width="100%",
        on_mount=DashboardRealtimeState.start_streaming
    )