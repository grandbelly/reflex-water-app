"""
Sensor Service with Eager SQL (greenlet-safe)
- raw SQL + dict rows
- single roundtrip for charts (window function)
- SET LOCAL statement_timeout
"""
from typing import List, Dict
from datetime import datetime
import pytz
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from reflex.utils import console


class SensorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_sensors_with_latest(self) -> List[Dict]:
        """Get all sensors with latest values - greenlet safe"""
        try:
            # 쿼리 타임아웃(예: 5초)
            await self.session.execute(text("SET LOCAL statement_timeout = '5s'"))

            q = text("""
                SELECT
                  l.tag_name,
                  l.value,
                  l.ts AS ts_utc,
                  COALESCE(l.quality, 0) AS quality,
                  COALESCE(q.min_val, 0.0) AS min_val,
                  COALESCE(q.max_val, 100.0) AS max_val,
                  COALESCE(q.warning_low, 20.0) AS warning_low,
                  COALESCE(q.warning_high, 80.0) AS warning_high,
                  CASE
                    WHEN l.value IS NULL OR q.min_val IS NULL THEN 0
                    WHEN l.value < q.min_val OR l.value > q.max_val THEN 2
                    WHEN l.value < q.warning_low OR l.value > q.warning_high THEN 1
                    ELSE 0
                  END AS status
                FROM influx_latest l
                LEFT JOIN influx_qc_rule q ON l.tag_name = q.tag_name
                ORDER BY l.tag_name
            """)

            rows = (await self.session.execute(q)).mappings().all()

            # UTC를 KST로 변환
            kst = pytz.timezone('Asia/Seoul')
            result = []

            for r in rows:
                # timestamp 변환
                timestamp_str = None
                if r["ts_utc"]:
                    # UTC datetime을 KST로 변환
                    if r["ts_utc"].tzinfo is None:
                        # naive datetime이면 UTC로 간주
                        ts_utc = pytz.UTC.localize(r["ts_utc"])
                    else:
                        ts_utc = r["ts_utc"]
                    ts_kst = ts_utc.astimezone(kst)
                    timestamp_str = ts_kst.strftime("%Y-%m-%d %H:%M:%S")

                result.append({
                    "tag_name": r["tag_name"],
                    "value": float(r["value"]) if r["value"] is not None else 0.0,
                    "timestamp": timestamp_str,
                    "quality": int(r["quality"]),
                    "status": int(r["status"]),
                    "qc_rule": {
                        "min_val": float(r["min_val"]),
                        "max_val": float(r["max_val"]),
                        "warning_low": float(r["warning_low"]),
                        "warning_high": float(r["warning_high"]),
                    },
                })

            console.info(f"Loaded {len(result)} sensors with raw SQL")
            return result

        except Exception as e:
            console.error(f"Error fetching sensors: {e}")
            return []

    async def get_aggregated_chart_data(self, tag_names: List[str]) -> Dict[str, List[Dict]]:
        """Get chart data with single roundtrip - window function"""
        try:
            # 쿼리 타임아웃
            await self.session.execute(text("SET LOCAL statement_timeout = '5s'"))

            # 한 번의 라운드트립: 태그별 최근 20개 버킷만 남기고 오름차순으로 정렬
            q = text("""
                WITH bucketed AS (
                  SELECT
                    tag_name,
                    date_trunc('minute', ts) AS time,
                    avg(value) AS value
                  FROM influx_hist
                  WHERE tag_name = ANY(:tags)
                    AND ts > NOW() - INTERVAL '20 minutes'
                  GROUP BY tag_name, time
                ),
                ranked AS (
                  SELECT
                    tag_name, time, value,
                    row_number() OVER (PARTITION BY tag_name ORDER BY time DESC) AS rn
                  FROM bucketed
                )
                SELECT tag_name, time, value
                FROM ranked
                WHERE rn <= :limit
                ORDER BY tag_name, time ASC
            """)

            params = {"tags": tag_names, "limit": 20}
            rows = (await self.session.execute(q, params)).mappings().all()

            out: Dict[str, List[Dict]] = {}
            kst = pytz.timezone('Asia/Seoul')
            for r in rows:
                # Convert UTC to KST for display
                if r["time"]:
                    if r["time"].tzinfo is None:
                        time_utc = pytz.UTC.localize(r["time"])
                    else:
                        time_utc = r["time"]
                    time_kst = time_utc.astimezone(kst)
                    time_str = time_kst.strftime("%H:%M")
                else:
                    time_str = ""

                out.setdefault(r["tag_name"], []).append({
                    "time": time_str,
                    "timestamp": time_kst.strftime("%Y-%m-%d %H:%M:%S") if r["time"] else "",
                    "value": float(r["value"]) if r["value"] is not None else 0.0,
                })

            return out

        except Exception as e:
            console.error(f"Error fetching chart data: {e}")
            return {}

    async def get_sensor_statistics(self) -> Dict[str, int]:
        """Get sensor statistics with optimized query"""
        try:
            await self.session.execute(text("SET LOCAL statement_timeout = '5s'"))

            q = text("""
                WITH status_calc AS (
                  SELECT
                    CASE
                      WHEN l.value IS NULL OR q.min_val IS NULL THEN 0
                      WHEN l.value < q.min_val OR l.value > q.max_val THEN 2
                      WHEN l.value < q.warning_low OR l.value > q.warning_high THEN 1
                      ELSE 0
                    END AS status
                  FROM influx_latest l
                  LEFT JOIN influx_qc_rule q ON l.tag_name = q.tag_name
                )
                SELECT
                  COUNT(*) FILTER (WHERE status = 0) AS normal,
                  COUNT(*) FILTER (WHERE status = 1) AS warning,
                  COUNT(*) FILTER (WHERE status = 2) AS critical
                FROM status_calc
            """)

            row = (await self.session.execute(q)).mappings().one()

            return {
                "normal": int(row["normal"] or 0),
                "warning": int(row["warning"] or 0),
                "critical": int(row["critical"] or 0),
            }

        except Exception as e:
            console.error(f"Error fetching statistics: {e}")
            return {"normal": 0, "warning": 0, "critical": 0}