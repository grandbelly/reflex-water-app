"""
Alarm Service - Rule-based alarm management
- Uses raw SQL with AsyncSession (matches alarm_history schema)
- Returns dict (not ORM objects)
- Follows Dashboard/Communication service pattern
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import pytz
from reflex.utils import console


class AlarmService:
    """Alarm data service using raw SQL - matches real alarm_history schema"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_rule_based_alarms(
        self,
        hours: int = 24,
        limit: int = 100,
        scenario_filter: str = "RULE_BASE"
    ) -> List[Dict[str, Any]]:
        """
        Get RULE_BASE alarms from recent hours

        Args:
            hours: Look back hours (default 24)
            limit: Max results (default 100)
            scenario_filter: Scenario filter (default RULE_BASE)

        Returns:
            List of alarm dicts with tag, level, message, etc.
        """
        try:
            await self.session.execute(text("SET LOCAL statement_timeout = '10s'"))

            q = text("""
                SELECT
                    event_id,
                    scenario_id,
                    level,
                    triggered_at,
                    message,
                    sensor_data->>'tag_name' as tag_name,
                    sensor_data->>'sensor_type' as sensor_type,
                    (sensor_data->>'value')::numeric as value,
                    sensor_data->>'unit' as unit,
                    (sensor_data->>'threshold_low')::numeric as threshold_low,
                    (sensor_data->>'threshold_high')::numeric as threshold_high,
                    sensor_data->>'cause' as cause,
                    acknowledged,
                    acknowledged_by,
                    acknowledged_at,
                    resolved,
                    resolved_at
                FROM alarm_history
                WHERE scenario_id = :scenario_id
                  AND triggered_at >= NOW() - :hours * INTERVAL '1 hour'
                ORDER BY triggered_at DESC
                LIMIT :limit
            """)

            result = await self.session.execute(q, {
                "scenario_id": scenario_filter,
                "hours": hours,
                "limit": limit
            })
            rows = result.mappings().all()

            # Convert to KST and format
            kst = pytz.timezone('Asia/Seoul')
            alarms = []

            for row in rows:
                triggered_at = row["triggered_at"]
                triggered_at_kst = triggered_at.astimezone(kst) if triggered_at else None

                alarms.append({
                    "event_id": row["event_id"],
                    "scenario_id": row["scenario_id"],
                    "level": int(row["level"]),
                    "level_name": self._get_level_name(int(row["level"])),
                    "triggered_at": triggered_at_kst.strftime("%Y-%m-%d %H:%M:%S") if triggered_at_kst else "",
                    "triggered_at_short": triggered_at_kst.strftime("%m-%d %H:%M") if triggered_at_kst else "",
                    "message": row["message"],
                    "tag_name": row["tag_name"],
                    "sensor_type": row["sensor_type"],
                    "value": float(row["value"]) if row["value"] else 0.0,
                    "unit": row["unit"] or "",
                    "threshold_low": float(row["threshold_low"]) if row["threshold_low"] else None,
                    "threshold_high": float(row["threshold_high"]) if row["threshold_high"] else None,
                    "cause": row["cause"] or "",
                    "acknowledged": bool(row["acknowledged"]),
                    "acknowledged_by": row["acknowledged_by"] or "",
                    "resolved": bool(row["resolved"]),
                })

            console.info(f"Loaded {len(alarms)} RULE_BASE alarms (last {hours}h)")
            return alarms

        except Exception as e:
            console.error(f"Failed to load rule-based alarms: {e}")
            return []

    async def get_alarm_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get alarm statistics for dashboard

        Args:
            hours: Look back hours (default 24)

        Returns:
            Dict with counts by level and status
        """
        try:
            await self.session.execute(text("SET LOCAL statement_timeout = '5s'"))

            q = text("""
                SELECT
                    level,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE acknowledged = false) as unacknowledged,
                    COUNT(*) FILTER (WHERE resolved = false) as unresolved
                FROM alarm_history
                WHERE triggered_at >= NOW() - :hours * INTERVAL '1 hour'
                  AND scenario_id = 'RULE_BASE'
                GROUP BY level
                ORDER BY level DESC
            """)

            result = await self.session.execute(q, {"hours": hours})
            rows = result.mappings().all()

            # Aggregate statistics
            stats = {
                "total": 0,
                "critical": 0,      # level 5
                "error": 0,         # level 4
                "warning": 0,       # level 3
                "info": 0,          # level 2
                "caution": 0,       # level 1
                "unacknowledged": 0,
                "unresolved": 0,
            }

            for row in rows:
                level = int(row["level"])
                count = int(row["count"])

                stats["total"] += count
                stats["unacknowledged"] += int(row["unacknowledged"])
                stats["unresolved"] += int(row["unresolved"])

                # Map level to category
                if level == 5:
                    stats["critical"] += count
                elif level == 4:
                    stats["error"] += count
                elif level == 3:
                    stats["warning"] += count
                elif level == 2:
                    stats["info"] += count
                elif level == 1:
                    stats["caution"] += count

            console.info(f"Alarm stats: {stats['total']} total, {stats['critical']} critical, {stats['warning']} warning")
            return stats

        except Exception as e:
            console.error(f"Failed to get alarm statistics: {e}")
            return {
                "total": 0,
                "critical": 0,
                "error": 0,
                "warning": 0,
                "info": 0,
                "caution": 0,
                "unacknowledged": 0,
                "unresolved": 0,
            }

    async def acknowledge_alarm(
        self,
        event_id: str,
        acknowledged_by: str = "system"
    ) -> bool:
        """
        Acknowledge an alarm

        Args:
            event_id: Alarm event ID (primary key)
            acknowledged_by: User who acknowledged

        Returns:
            True if successful
        """
        try:
            await self.session.execute(text("SET LOCAL statement_timeout = '5s'"))

            q = text("""
                UPDATE alarm_history
                SET
                    acknowledged = true,
                    acknowledged_by = :acknowledged_by,
                    acknowledged_at = NOW()
                WHERE event_id = :event_id
            """)

            await self.session.execute(q, {
                "event_id": event_id,
                "acknowledged_by": acknowledged_by
            })
            await self.session.commit()

            console.info(f"Acknowledged alarm {event_id} by {acknowledged_by}")
            return True

        except Exception as e:
            console.error(f"Failed to acknowledge alarm {event_id}: {e}")
            await self.session.rollback()
            return False

    @staticmethod
    def _get_level_name(level: int) -> str:
        """Convert level number to name"""
        level_map = {
            5: "CRITICAL",
            4: "ERROR",
            3: "WARNING",
            2: "INFO",
            1: "CAUTION"
        }
        return level_map.get(level, "UNKNOWN")