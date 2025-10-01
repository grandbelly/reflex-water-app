"""SCADA 알람 비교 뷰어 - 룰 베이스 vs AI 베이스"""

import reflex as rx
from water_app.states.cps_only.scada_alarm_comparison_state import ScadaAlarmComparisonState
from datetime import datetime


def alarm_severity_badge(severity: int) -> rx.Component:
    """심각도 배지"""
    color_map = {
        1: "blue",
        2: "green",
        3: "yellow",
        4: "orange",
        5: "red"
    }
    label_map = {
        1: "정보",
        2: "주의",
        3: "경고",
        4: "위험",
        5: "긴급"
    }
    return rx.badge(
        label_map.get(severity, "알 수 없음"),
        color_scheme=color_map.get(severity, "gray"),
        variant="solid",
        size="2"
    )


def method_badge(method: str) -> rx.Component:
    """알람 방식 배지"""
    if method == "RULE_BASE":
        return rx.badge("룰 베이스", color_scheme="blue", variant="outline")
    elif method == "AI_BASE":
        return rx.badge("AI 베이스", color_scheme="purple", variant="outline")
    else:
        return rx.badge(method, color_scheme="gray", variant="outline")


def comparison_table() -> rx.Component:
    """알람 비교 테이블"""
    return rx.box(
        rx.vstack(
            # 헤더
            rx.hstack(
                rx.heading("SCADA 알람 비교 분석", size="5"),
                rx.spacer(),
                rx.hstack(
                    rx.text(f"총 {ScadaAlarmComparisonState.total_pairs}쌍", size="2"),
                    rx.button(
                        rx.icon(tag="refresh_cw", size=16),
                        "새로고침",
                        on_click=ScadaAlarmComparisonState.load_comparison_data,
                        size="2",
                        variant="outline"
                    ),
                    rx.button(
                        rx.icon(tag="activity", size=16),
                        "테스트 생성",
                        on_click=ScadaAlarmComparisonState.generate_test_data,
                        size="2",
                        color_scheme="green"
                    ),
                    spacing="2"
                ),
                width="100%",
                justify="between",
                align="center",
                padding_bottom="1em"
            ),

            # 통계 카드
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.text("룰 베이스", size="2", weight="bold"),
                        rx.text(ScadaAlarmComparisonState.rule_count.to_string(), size="4"),
                        rx.text(f"평균 응답: <10ms", size="1", color="gray"),
                        spacing="1"
                    ),
                    width="100%"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("AI 베이스", size="2", weight="bold"),
                        rx.text(ScadaAlarmComparisonState.ai_count.to_string(), size="4"),
                        rx.text(f"평균 응답: {ScadaAlarmComparisonState.avg_ai_response}s",
                               size="1", color="gray"),
                        spacing="1"
                    ),
                    width="100%"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("일치율", size="2", weight="bold"),
                        rx.text(f"{ScadaAlarmComparisonState.match_rate}%", size="4"),
                        rx.text("레벨 일치도", size="1", color="gray"),
                        spacing="1"
                    ),
                    width="100%"
                ),
                width="100%",
                spacing="3",
                padding_bottom="1em"
            ),

            # 비교 테이블
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("시간", width="150px"),
                            rx.table.column_header_cell("센서", width="100px"),
                            rx.table.column_header_cell("값", width="100px"),
                            rx.table.column_header_cell("레벨", width="80px"),
                            rx.table.column_header_cell("룰 메시지", min_width="250px"),
                            rx.table.column_header_cell("AI 메시지", min_width="250px"),
                            rx.table.column_header_cell("응답시간", width="100px"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            ScadaAlarmComparisonState.comparison_data,
                            lambda item: rx.table.row(
                                rx.table.cell(
                                    rx.text(item["timestamp"], size="2", font_family="monospace")
                                ),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.badge(item["tag_name"], variant="outline"),
                                        rx.text(item["sensor_type"], size="1", color="gray"),
                                        spacing="1"
                                    )
                                ),
                                rx.table.cell(
                                    rx.text(f"{item['value']}{item['unit']}",
                                           font_weight="bold")
                                ),
                                rx.table.cell(
                                    alarm_severity_badge(item["level"])
                                ),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(item["rule_message"], size="2"),
                                        rx.text(f"원인: {item['rule_cause']}",
                                               size="1", color="orange"),
                                        rx.text(f"조치: {item['rule_action']}",
                                               size="1", color="blue"),
                                        spacing="1"
                                    )
                                ),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(item["ai_message"], size="2"),
                                        rx.text(f"원인: {item['ai_cause']}",
                                               size="1", color="orange"),
                                        rx.text(f"조치: {item['ai_action']}",
                                               size="1", color="blue"),
                                        spacing="1"
                                    )
                                ),
                                rx.table.cell(
                                    rx.cond(
                                        item["ai_response_time"] != "",
                                        rx.text(f"{item['ai_response_time']}s",
                                               size="2", color="purple"),
                                        rx.text("N/A", size="2", color="gray")
                                    )
                                ),
                                background_color=rx.cond(
                                    item["is_new"],
                                    "rgba(255, 255, 0, 0.1)",
                                    "transparent"
                                ),
                                _hover={"background_color": "rgba(255, 255, 255, 0.05)"}
                            )
                        )
                    ),
                    variant="surface",
                    size="2",
                    width="100%"
                ),
                height="500px",
                overflow_y="auto",
                border="1px solid rgba(255, 255, 255, 0.1)",
                border_radius="8px"
            ),

            # 분석 섹션
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.heading("메시지 품질 분석", size="3"),
                        rx.hstack(
                            rx.text("평균 길이:", size="2"),
                            rx.text(f"룰: {ScadaAlarmComparisonState.avg_rule_length}자",
                                   size="2", color="blue"),
                            rx.text(f"AI: {ScadaAlarmComparisonState.avg_ai_length}자",
                                   size="2", color="purple"),
                            spacing="2"
                        ),
                        spacing="2"
                    ),
                    width="100%"
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("성능 비교", size="3"),
                        rx.text(f"AI 평균 응답시간: {ScadaAlarmComparisonState.avg_ai_response}초",
                               size="2"),
                        rx.text(f"룰 베이스: <10ms (고정)", size="2"),
                        spacing="2"
                    ),
                    width="100%"
                ),
                width="100%",
                spacing="3",
                padding_top="1em"
            ),

            spacing="4",
            width="100%"
        ),
        padding="1em",
        width="100%"
    )


def scada_alarm_comparison() -> rx.Component:
    """SCADA 알람 비교 페이지"""
    return rx.vstack(
        comparison_table(),
        spacing="4",
        width="100%",
        on_mount=ScadaAlarmComparisonState.initialize
    )