"""개선된 트렌드 페이지 - 집계 뷰 직접 선택 가능"""
import reflex as rx
from water_app.states.common.trend_state import TrendState as T
from water_app.states.common.base import BaseState  # sidebar_collapsed를 위해 필요
from ..components.layout import shell


def _create_gradient(color: str, id: str):
    """차트용 그라데이션 정의"""
    return rx.el.defs(
        rx.el.linear_gradient(
            rx.el.stop(offset="0%", stop_color=color, stop_opacity=0.3),
            rx.el.stop(offset="95%", stop_color=color, stop_opacity=0.05),
            id=id,
            x1="0", y1="0", x2="0", y2="1"
        )
    )


def chart_mode_selector() -> rx.Component:
    """차트 모드 선택자"""
    return rx.segmented_control.root(
        rx.segmented_control.item("Area", value="area"),
        rx.segmented_control.item("Line", value="line"),
        rx.segmented_control.item("Bar", value="bar"),
        rx.segmented_control.item("Composed", value="composed"),
        value=T.chart_mode,
        size="2",
        on_change=T.set_chart_mode
    )

def trend_toggle_group() -> rx.Component:
    """트렌드 선택 세그먼트 컨트롤"""
    return rx.segmented_control.root(
        rx.segmented_control.item("Average", value="avg"),
        rx.segmented_control.item("Minimum", value="min"),
        rx.segmented_control.item("Maximum", value="max"),
        rx.segmented_control.item("First", value="first"),
        rx.segmented_control.item("Last", value="last"),
        value=T.trend_selected,
        on_change=T.set_trend_selected,
        disabled=rx.cond(T.chart_mode == "composed", True, False),
        size="2"
    )


def aggregation_info_badge() -> rx.Component:
    """현재 선택된 집계 뷰와 시간 범위를 표시하는 배지"""
    aggregation_labels = {
        "1m": "1분 집계",
        "10m": "10분 집계",
        "1h": "1시간 집계",
        "1d": "1일 집계"
    }

    time_range_labels = {
        "1h": "최근 1시간",
        "24h": "최근 24시간",
        "7d": "최근 7일",
        "30d": "최근 30일"
    }

    return rx.hstack(
        rx.badge(
            rx.hstack(
                rx.icon("database", size=12),
                rx.text(
                    rx.cond(
                        T.aggregation_view == "1m", "1분 집계",
                        rx.cond(
                            T.aggregation_view == "10m", "10분 집계",
                            rx.cond(
                                T.aggregation_view == "1h", "1시간 집계",
                                rx.cond(
                                    T.aggregation_view == "1d", "1일 집계",
                                    "알 수 없음"
                                )
                            )
                        )
                    ),
                    size="1"
                ),
                spacing="1"
            ),
            color_scheme="blue",
            variant="soft"
        ),
        rx.badge(
            rx.hstack(
                rx.icon("clock", size=12),
                rx.text(
                    T.time_range_label,
                    size="1"
                ),
                spacing="1"
            ),
            color_scheme="green",
            variant="soft"
        ),
        spacing="2"
    )


def trend_chart_area() -> rx.Component:
    """개선된 차트 영역 - 반응형 및 다양한 차트 타입 지원"""

    # 로딩 인디케이터
    loading_spinner = rx.center(
        rx.vstack(
            rx.spinner(size="3", color="blue"),
            rx.text("데이터 로딩 중...", size="3", color="gray"),
            spacing="3"
        ),
        width="100%",
        height="400px"
    )

    # 데이터 없음 표시
    no_data_message = rx.center(
        rx.vstack(
            rx.icon("alert-circle", size=48, color="gray"),
            rx.text("차트 데이터가 없습니다", size="4", weight="bold", color="gray"),
            rx.text("필터를 조정하고 다시 로드하세요", size="2", color="gray"),
            spacing="3"
        ),
        width="100%",
        height="400px"
    )

    # Area Chart
    area_chart = rx.box(
        rx.recharts.area_chart(
            _create_gradient("#3b82f6", "blueGradient"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
                stroke="#f3f4f6",
                opacity=0.5
            ),
            rx.recharts.area(
                data_key=T.trend_selected,
                stroke="#3b82f6",
                fill="url(#blueGradient)",
                type_="monotone",
                stroke_width=2,
                dot={"r": 2, "fill": "#3b82f6"},  # 실제 데이터 포인트 표시
                active_dot={"r": 4, "fill": "#1d4ed8"}  # 호버 시 강조
            ),
            rx.recharts.x_axis(
                data_key="bucket_formatted",
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 10, "angle": -45, "textAnchor": "end"},
                height=50
            ),
            rx.recharts.y_axis(
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 11},
                domain=["dataMin - 5", "dataMax + 5"]
            ),
            rx.recharts.tooltip(
                content_style={
                    "backgroundColor": "white",
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                }
            ),
            rx.recharts.legend(
                vertical_align="top",
                height=36
            ),
            data=T.series_for_tag,
            width="100%",
            height=400,
            margin={"top": 40, "right": 30, "bottom": 30, "left": 60}
        ),
        width="100%"
    )

    # Line Chart
    line_chart = rx.box(
        rx.recharts.line_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
                stroke="#f3f4f6"
            ),
            rx.recharts.line(
                data_key=T.trend_selected,
                stroke="#3b82f6",
                stroke_width=2,
                dot={"r": 3},
                active_dot={"r": 5}
            ),
            rx.recharts.x_axis(
                data_key="bucket_formatted",
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 10, "angle": -45, "textAnchor": "end"},
                height=50
            ),
            rx.recharts.y_axis(
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 11}
            ),
            rx.recharts.tooltip(),
            rx.recharts.legend(
                vertical_align="top",
                height=36
            ),
            data=T.series_for_tag,
            width="100%",
            height=400,
            margin={"top": 40, "right": 30, "bottom": 30, "left": 60}
        ),
        width="100%"
    )

    # Bar Chart
    bar_chart = rx.box(
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
                stroke="#f3f4f6"
            ),
            rx.recharts.bar(
                data_key=T.trend_selected,
                fill="#3b82f6",
                radius=[4, 4, 0, 0]
            ),
            rx.recharts.x_axis(
                data_key="bucket_formatted",
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 10, "angle": -45, "textAnchor": "end"},
                height=50
            ),
            rx.recharts.y_axis(
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 11}
            ),
            rx.recharts.tooltip(),
            rx.recharts.legend(
                vertical_align="top",
                height=36
            ),
            data=T.series_for_tag,
            width="100%",
            height=400,
            margin={"top": 40, "right": 30, "bottom": 50, "left": 60}
        ),
        width="100%"
    )

    # Composed Chart (Line + Bar)
    composed_chart = rx.box(
        rx.recharts.composed_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
                stroke="#f3f4f6"
            ),
            rx.recharts.bar(
                data_key="avg",
                fill="#e0e7ff",
                fill_opacity=0.8,
                name="Average"
            ),
            rx.recharts.line(
                data_key="max",
                stroke="#ef4444",
                stroke_width=2,
                dot=False,
                name="Maximum"
            ),
            rx.recharts.line(
                data_key="min",
                stroke="#10b981",
                stroke_width=2,
                dot=False,
                name="Minimum"
            ),
            rx.recharts.x_axis(
                data_key="bucket_formatted",
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 10, "angle": -45, "textAnchor": "end"},
                height=50
            ),
            rx.recharts.y_axis(
                stroke="#e5e7eb",
                tick={"fill": "#6b7280", "fontSize": 11}
            ),
            rx.recharts.tooltip(),
            rx.recharts.legend(
                vertical_align="top",
                height=36
            ),
            data=T.series_for_tag,
            width="100%",
            height=400,
            margin={"top": 40, "right": 30, "bottom": 50, "left": 60}
        ),
        width="100%"
    )

    # 로딩 중이면 스피너 표시
    return rx.cond(
        T.loading,
        loading_spinner,
        # 로딩이 아니면 데이터 체크
        rx.cond(
            T.series_for_tag,
            # 데이터가 있으면 차트 표시
            rx.cond(
                T.chart_mode == "line",
                line_chart,
                rx.cond(
                    T.chart_mode == "bar",
                    bar_chart,
                    rx.cond(
                        T.chart_mode == "composed",
                        composed_chart,
                        area_chart  # default
                    )
                )
            ),
            # 데이터가 없으면 메시지 표시
            no_data_message
        )
    )


def trend_page_enhanced_v2() -> rx.Component:
    """개선된 트렌드 페이지 v2"""
    return shell(
        rx.vstack(
            # 상단 컨트롤 영역 - Modern card-based layout
            rx.card(
                rx.vstack(
                    # Header with title and action button
                    rx.flex(
                        rx.hstack(
                            rx.icon("sliders", size=20, color=rx.color("blue", 9)),
                            rx.heading("D100 센서 트렌드", size="5", weight="bold"),
                            spacing="2",
                            align="center"
                        ),
                        rx.button(
                            rx.icon("refresh-cw", size=16),
                            " 새로고침",
                            on_click=T.load,
                            variant="soft",
                            color_scheme="blue",
                            size="2",
                        ),
                        justify="between",
                        align="center",
                        width="100%"
                    ),

                    rx.divider(),

                    # Filter controls in responsive grid with compact boxes
                    rx.grid(
                        # Tag selection - compact box
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("tag", size=14, color=rx.color("blue", 9)),
                                    rx.text("태그 선택", size="2", weight="medium", color=rx.color("gray", 11)),
                                    spacing="1",
                                    align="center"
                                ),
                                rx.select(
                                    T.tags,
                                    value=T.tag_name,
                                    on_change=T.set_tag_select,
                                    placeholder="선택하세요",
                                    size="2",
                                    width="100%"
                                ),
                                spacing="2",
                                width="100%"
                            ),
                            padding="3",
                            border_radius="md",
                            bg=rx.color("blue", 2),
                            border=f"1px solid {rx.color('blue', 4)}"
                        ),

                        # Aggregation selection - compact box
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("layers", size=14, color=rx.color("green", 9)),
                                    rx.text("집계 단위", size="2", weight="medium", color=rx.color("gray", 11)),
                                    spacing="1",
                                    align="center"
                                ),
                                rx.select(
                                    ["1m", "10m", "1h", "1d"],
                                    value=T.aggregation_view,
                                    on_change=T.set_aggregation_view,
                                    placeholder="선택하세요",
                                    size="2",
                                    width="100%"
                                ),
                                spacing="2",
                                width="100%"
                            ),
                            padding="3",
                            border_radius="md",
                            bg=rx.color("green", 2),
                            border=f"1px solid {rx.color('green', 4)}"
                        ),

                        # Time range selection - compact box
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("calendar", size=14, color=rx.color("orange", 9)),
                                    rx.text("조회 기간", size="2", weight="medium", color=rx.color("gray", 11)),
                                    spacing="1",
                                    align="center"
                                ),
                                rx.select(
                                    T.time_range_labels,
                                    value=T.time_range_display,
                                    on_change=T.set_time_range,
                                    placeholder="선택하세요",
                                    size="2",
                                    width="100%"
                                ),
                                spacing="2",
                                width="100%"
                            ),
                            padding="3",
                            border_radius="md",
                            bg=rx.color("orange", 2),
                            border=f"1px solid {rx.color('orange', 4)}"
                        ),

                        columns=rx.breakpoints(
                            initial="1",
                            xs="1",
                            sm="2",
                            md="3",
                            lg="3",
                            xl="3"
                        ),
                        gap="3",
                        width="100%"
                    ),

                    # Current selection summary with modern badges
                    rx.divider(),
                    rx.flex(
                        # Current tag badge
                        rx.badge(
                            rx.icon("activity", size=12),
                            " ",
                            rx.cond(
                                T.tag_name,
                                T.tag_name,
                                "선택 안됨"
                            ),
                            color_scheme="purple",
                            variant="soft",
                            size="2"
                        ),

                        rx.spacer(),

                        # Status indicators
                        aggregation_info_badge(),

                        spacing="2",
                        align="center",
                        width="100%"
                    ),

                    spacing="4",
                    width="100%"
                ),
                size="3",
                width="100%"
            ),

            # 차트 영역 - 반응형 개선
            rx.card(
                rx.vstack(
                    # 차트 타입 선택과 데이터 선택
                    rx.flex(
                        rx.vstack(
                            rx.text("차트 타입", size="2", weight="medium", color="gray"),
                            chart_mode_selector(),
                            spacing="1",
                            align="start"
                        ),

                        # Composed 모드가 아닐 때만 데이터 선택 표시
                        rx.cond(
                            T.chart_mode != "composed",
                            rx.fragment(
                                rx.spacer(),
                                rx.vstack(
                                    rx.text("데이터 선택", size="2", weight="medium", color="gray"),
                                    trend_toggle_group(),
                                    spacing="1",
                                    align="start"
                                )
                            ),
                            # Composed 모드일 때 설명 표시
                            rx.fragment(
                                rx.spacer(),
                                rx.vstack(
                                    rx.text("차트 정보", size="2", weight="medium", color="gray"),
                                    rx.badge(
                                        rx.icon("info", size=12),
                                        " Avg, Max, Min 자동 표시",
                                        color_scheme="blue",
                                        variant="soft",
                                        size="2"
                                    ),
                                    spacing="1",
                                    align="start"
                                )
                            )
                        ),

                        width="100%",
                        align="start",
                        justify="start"
                    ),

                    rx.divider(),

                    # 차트 렌더링 - 반응형 컨테이너
                    rx.box(
                        trend_chart_area(),
                        width="100%",
                        min_height="400px",
                        style={
                            "resize": "vertical",
                            "overflow": "auto"
                        }
                    ),

                    spacing="3",
                    width="100%"
                ),
                class_name="mb-4",
                width="100%"
            ),

            # 데이터 테이블 - 반응형 개선
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Historical Data", size="4", weight="bold"),
                        rx.spacer(),
                        rx.hstack(
                            # 데이터 개수
                            rx.badge(
                                rx.cond(
                                    T.series_for_tag,
                                    rx.fragment(
                                        rx.text(T.series_count_s),
                                        " / ",
                                        rx.text(T.expected_data_count),
                                        " rows"
                                    ),
                                    "No data"
                                ),
                                color_scheme="gray"
                            ),
                            # 데이터 완전성
                            rx.cond(
                                T.series_for_tag,
                                rx.badge(
                                    rx.icon("activity", size=14),
                                    " ",
                                    T.data_completeness,
                                    color_scheme=rx.cond(
                                        T.missing_data_count > 0,
                                        "orange",
                                        "green"
                                    ),
                                    variant="soft"
                                ),
                                rx.fragment()
                            ),
                            # 결측 데이터
                            rx.cond(
                                T.missing_data_count > 0,
                                rx.badge(
                                    rx.icon("alert-circle", size=14),
                                    " ",
                                    T.missing_data_count,
                                    " missing",
                                    color_scheme="red",
                                    variant="soft"
                                ),
                                rx.fragment()
                            ),
                            rx.button(
                                rx.icon("download", size=16),
                                "CSV 내보내기",
                                on_click=T.export_csv,
                                variant="soft",
                                color_scheme="green",
                                size="2",
                                disabled=rx.cond(T.series_for_tag, False, True)
                            ),
                            spacing="3"
                        ),
                        align="center",
                        width="100%"
                    ),

                    rx.divider(),

                    rx.cond(
                        T.series_for_tag,
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("No."),
                                        rx.table.column_header_cell("Tag"),
                                        rx.table.column_header_cell("Timestamp"),
                                        rx.table.column_header_cell("Average"),
                                        rx.table.column_header_cell("Min"),
                                        rx.table.column_header_cell("Max"),
                                        rx.table.column_header_cell("Last"),
                                        rx.table.column_header_cell("First"),
                                        rx.table.column_header_cell("Count")
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        T.series_for_tag_desc_with_num,
                                        lambda row: rx.table.row(
                                            rx.table.cell(row["No"]),
                                            rx.table.cell(row["Tag"]),
                                            rx.table.cell(
                                                row["Timestamp"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#ef4444", "fontWeight": "500"},
                                                    {}
                                                )
                                            ),
                                            rx.table.cell(
                                                row["Average"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#9ca3af", "fontStyle": "italic"},
                                                    {}
                                                )
                                            ),
                                            rx.table.cell(
                                                row["Min"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#9ca3af", "fontStyle": "italic"},
                                                    {}
                                                )
                                            ),
                                            rx.table.cell(
                                                row["Max"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#9ca3af", "fontStyle": "italic"},
                                                    {}
                                                )
                                            ),
                                            rx.table.cell(
                                                row["Last"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#9ca3af", "fontStyle": "italic"},
                                                    {}
                                                )
                                            ),
                                            rx.table.cell(
                                                row["First"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#9ca3af", "fontStyle": "italic"},
                                                    {}
                                                )
                                            ),
                                            rx.table.cell(
                                                row["Count"],
                                                style=rx.cond(
                                                    row.get("Missing", False),
                                                    {"color": "#9ca3af", "fontStyle": "italic"},
                                                    {}
                                                )
                                            ),
                                            style=rx.cond(
                                                row.get("Missing", False),
                                                {"backgroundColor": "#fef2f2"},
                                                {}
                                            )
                                        )
                                    )
                                ),
                                width="100%",
                                variant="surface",
                                size="2"
                            ),
                            class_name="w-full overflow-x-auto"
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("database", size=48, color="gray"),
                                rx.text("데이터가 없습니다", size="3", color="gray"),
                                rx.text("태그를 선택하고 조회 기간을 설정하세요", size="2", color="gray"),
                                spacing="3",
                                align="center"
                            ),
                            height="300px",
                            class_name="border-2 border-dashed border-gray-200 rounded-lg"
                        )
                    ),

                    spacing="3",
                    width="100%"
                ),
                width="100%"
            ),

            spacing="4",
            width="100%",
            class_name="p-4 max-w-full"
        ),
        active_route="/trend",
        on_mount=T.load
    )