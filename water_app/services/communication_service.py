"""
Communication Service
- Handles communication statistics queries
- Returns data for heatmap and analytics
"""
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy import text
from water_app.services.base_service import BaseService


class CommunicationService(BaseService):
    """Service for communication success rate monitoring"""

    async def get_available_tags(self) -> List[str]:
        """
        Get list of available sensor tags

        Returns:
            List of tag names
        """
        query = text("""
            SELECT DISTINCT tag_name
            FROM influx_latest
            ORDER BY tag_name
        """)

        rows = await self.execute_query(query, timeout="5s")
        return [row['tag_name'] for row in rows]

    async def get_hourly_stats(self, tag: str, days: int) -> List[Dict]:
        """
        Get hourly communication statistics

        Args:
            tag: Sensor tag name
            days: Number of days to look back

        Returns:
            List of hourly statistics with:
            - timestamp: Hour timestamp
            - record_count: Actual record count
            - expected_count: Expected record count (720 per hour = 5 sec interval)
            - success_rate: Percentage of expected records received
            - date: Date string
            - hour: Hour of day
        """
        query = text("""
            WITH hourly_data AS (
                SELECT
                    date_trunc('hour', ts) as timestamp,
                    COUNT(*) as record_count,
                    720 as expected_count
                FROM influx_hist
                WHERE ts >= NOW() - :days * INTERVAL '1 day'
                  AND ts < NOW()
                  AND tag_name = :tag
                GROUP BY date_trunc('hour', ts)
            )
            SELECT
                timestamp,
                record_count,
                expected_count,
                ROUND((record_count::NUMERIC / expected_count) * 100, 2) as success_rate,
                TO_CHAR(timestamp, 'YYYY-MM-DD') as date,
                EXTRACT(hour FROM timestamp) as hour
            FROM hourly_data
            ORDER BY timestamp DESC
        """)

        return await self.execute_query(
            query,
            {"days": days, "tag": tag},
            timeout="15s"  # Longer timeout for larger queries
        )

    async def get_daily_stats(self, days: int) -> List[Dict]:
        """
        Get daily statistics for all tags

        Args:
            days: Number of days to look back

        Returns:
            List of daily statistics with:
            - date: Date
            - tag_name: Sensor tag
            - daily_count: Records for the day
            - expected_daily_count: Expected records (17280 = 720 * 24)
            - success_rate: Percentage
        """
        query = text("""
            WITH daily_data AS (
                SELECT
                    date_trunc('day', ts) as date,
                    tag_name,
                    COUNT(*) as daily_count,
                    17280 as expected_daily_count
                FROM influx_hist
                WHERE ts >= NOW() - :days * INTERVAL '1 day'
                  AND ts < NOW()
                GROUP BY date_trunc('day', ts), tag_name
            )
            SELECT
                date,
                tag_name,
                daily_count,
                expected_daily_count,
                ROUND((daily_count::NUMERIC / expected_daily_count) * 100, 2) as success_rate
            FROM daily_data
            ORDER BY date DESC, tag_name
        """)

        return await self.execute_query(
            query,
            {"days": days},
            timeout="15s"
        )

    async def get_tag_summary(self, tag: str, days: int) -> Dict:
        """
        Get summary statistics for a specific tag

        Args:
            tag: Sensor tag name
            days: Number of days to look back

        Returns:
            Dict with summary stats:
            - total_records: Total records received
            - expected_records: Total expected records
            - success_rate: Overall success rate
            - active_hours: Number of hours with data
        """
        # Ensure days is int (防止 문자열 전달)
        days_int = int(days) if not isinstance(days, int) else days

        query = text("""
            WITH stats AS (
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT date_trunc('hour', ts)) as active_hours,
                    CAST(:expected_total AS NUMERIC) as expected_records
                FROM influx_hist
                WHERE ts >= NOW() - :days * INTERVAL '1 day'
                  AND ts < NOW()
                  AND tag_name = :tag
            )
            SELECT
                total_records,
                expected_records,
                active_hours,
                ROUND((total_records::NUMERIC / expected_records) * 100, 2) as success_rate
            FROM stats
        """)

        expected_total = days_int * 24 * 720  # days * hours * records_per_hour

        rows = await self.execute_query(
            query,
            {
                "tag": tag,
                "days": days_int,
                "expected_total": expected_total
            },
            timeout="10s"
        )

        if rows:
            return rows[0]
        else:
            return {
                "total_records": 0,
                "expected_records": expected_total,
                "active_hours": 0,
                "success_rate": 0.0
            }