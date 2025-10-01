"""
Communication State - Refactored with Service Pattern
- Uses CommunicationService for all database operations
- Direct rx.State inheritance (not BaseState to avoid conflicts)
- Pandas operations for data transformation
"""
import reflex as rx
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from water_app.db_orm import get_async_session
from water_app.services.communication_service import CommunicationService
from reflex.utils import console


class CommunicationState(rx.State):
    """Communication monitoring state with service pattern"""

    # UI Controls
    selected_tag: str = "D100"
    selected_days: int = 7

    # Data Storage (internal - will be transformed by computed properties)
    available_tags: List[str] = []
    _df_hourly: List[Dict] = []  # Raw hourly data
    _df_daily: List[Dict] = []   # Raw daily data
    _summary: Dict = {}          # Summary statistics

    # Loading state
    loading: bool = False
    error_message: str = ""

    # Database Session Management
    # =========================================================================

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get database session with proper cleanup"""
        async with get_async_session() as session:
            try:
                yield session
            except Exception as e:
                console.error(f"Session error: {e}")
                raise

    async def set_error(self, message: str):
        """Set error message"""
        async with self:
            self.error_message = message

    # Computed Properties
    # =========================================================================

    @rx.var
    def selected_days_str(self) -> str:
        """Radio group용 문자열 변환"""
        return str(self.selected_days)

    @rx.var
    def active_hours_str(self) -> str:
        """활성 시간 수"""
        return str(len(self._df_hourly))

    @rx.var
    def total_hours_str(self) -> str:
        """전체 시간 라벨"""
        return f"Out of {self.selected_days * 24} hours"

    @rx.var
    def overall_success_rate(self) -> float:
        """전체 성공률 (from summary or calculate)"""
        if self._summary:
            return float(self._summary.get('success_rate', 0.0))

        if not self._df_hourly:
            return 0.0

        df = pd.DataFrame(self._df_hourly)
        df['record_count'] = pd.to_numeric(df['record_count'], errors='coerce')
        df['expected_count'] = pd.to_numeric(df['expected_count'], errors='coerce')

        total_records = df['record_count'].sum()
        expected_records = df['expected_count'].sum()

        if expected_records > 0:
            return round(float(total_records / expected_records) * 100, 2)
        return 0.0

    @rx.var
    def total_records(self) -> int:
        """전체 레코드 수"""
        if self._summary:
            return int(self._summary.get('total_records', 0))

        if not self._df_hourly:
            return 0

        df = pd.DataFrame(self._df_hourly)
        df['record_count'] = pd.to_numeric(df['record_count'], errors='coerce')
        return int(df['record_count'].sum())

    @rx.var
    def expected_records(self) -> int:
        """예상 레코드 수"""
        if self._summary:
            return int(self._summary.get('expected_records', 0))

        if not self._df_hourly:
            return 0

        df = pd.DataFrame(self._df_hourly)
        df['expected_count'] = pd.to_numeric(df['expected_count'], errors='coerce')
        return int(df['expected_count'].sum())

    @rx.var
    def heatmap_matrix(self) -> List[List[float]]:
        """Pandas pivot_table로 히트맵 매트릭스 생성"""
        if not self._df_hourly:
            return [[0] * 24 for _ in range(self.selected_days)]

        try:
            df = pd.DataFrame(self._df_hourly)
            df['success_rate'] = pd.to_numeric(df['success_rate'], errors='coerce')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour

            # Pivot table로 매트릭스 생성
            pivot = df.pivot_table(
                values='success_rate',
                index='date',
                columns='hour',
                fill_value=0,
                aggfunc='mean'
            )

            # 모든 시간(0-23)이 포함되도록 reindex
            pivot = pivot.reindex(columns=range(24), fill_value=0)

            return pivot.values.tolist()
        except Exception as e:
            console.error(f"Heatmap matrix calculation failed: {e}")
            return [[0] * 24 for _ in range(self.selected_days)]

    @rx.var
    def hour_labels(self) -> List[str]:
        """시간 라벨 (00-23)"""
        return [f"{i:02d}" for i in range(24)]

    @rx.var
    def date_labels(self) -> List[str]:
        """날짜 라벨"""
        if not self._df_hourly:
            return []

        df = pd.DataFrame(self._df_hourly)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        dates = sorted(df['date'].unique())
        return [str(date) for date in dates]

    @rx.var
    def heatmap_dates(self) -> List[str]:
        """히트맵용 날짜 리스트"""
        return self.date_labels

    @rx.var
    def daily_chart_data(self) -> List[Dict]:
        """일별 트렌드 차트 데이터"""
        if not self._df_daily:
            return []

        df = pd.DataFrame(self._df_daily)
        df = df[df['tag_name'] == self.selected_tag].copy()
        df = df.sort_values('date')

        # 날짜 포맷팅
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%m/%d')

        return df[['date', 'success_rate']].to_dict('records')

    @rx.var
    def hourly_pattern_stats(self) -> Dict[str, Any]:
        """시간대별 패턴 분석 (Pandas 활용)"""
        if not self._df_hourly:
            return {"best_hour": "N/A", "worst_hour": "N/A", "std_dev": 0}

        try:
            df = pd.DataFrame(self._df_hourly)
            df['success_rate'] = df['success_rate'].astype(float)
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour

            # 시간대별 평균 성공률
            hourly_avg = df.groupby('hour')['success_rate'].mean()

            if not hourly_avg.empty:
                best_hour = hourly_avg.idxmax()
                worst_hour = hourly_avg.idxmin()
                std_dev = float(df['success_rate'].std())

                return {
                    "best_hour": f"{best_hour:02d}:00",
                    "worst_hour": f"{worst_hour:02d}:00",
                    "std_dev": round(std_dev, 2) if not pd.isna(std_dev) else 0
                }

            return {"best_hour": "N/A", "worst_hour": "N/A", "std_dev": 0}
        except Exception as e:
            console.error(f"Hourly pattern stats calculation failed: {e}")
            return {"best_hour": "N/A", "worst_hour": "N/A", "std_dev": 0}

    @rx.var
    def anomaly_detection(self) -> List[Dict]:
        """이상치 탐지 (Z-score 사용)"""
        if not self._df_hourly:
            return []

        try:
            df = pd.DataFrame(self._df_hourly)
            df['success_rate'] = pd.to_numeric(df['success_rate'], errors='coerce')

            # Z-score 계산
            mean = df['success_rate'].mean()
            std = df['success_rate'].std()

            if std > 0 and not pd.isna(std):
                df['z_score'] = np.abs((df['success_rate'] - mean) / std)
                anomalies = df[df['z_score'] > 2]  # Z-score > 2는 이상치

                if not anomalies.empty:
                    anomalies = anomalies.copy()
                    anomalies['timestamp'] = pd.to_datetime(anomalies['timestamp']).dt.strftime('%m/%d %H:%M')
                    anomalies['success_rate'] = anomalies['success_rate'].astype(float)
                    anomalies['z_score'] = anomalies['z_score'].astype(float)
                    return anomalies[['timestamp', 'success_rate', 'z_score']].round(2).to_dict('records')

            return []
        except Exception as e:
            console.error(f"Anomaly detection calculation failed: {e}")
            return []

    # Event Handlers
    # =========================================================================

    @rx.event(background=True)
    async def initialize(self):
        """초기화 - 태그 목록 로드 및 데이터 로드"""
        console.info("CommunicationState.initialize() called")

        async with self:
            self.loading = True

        try:
            # Fetch available tags
            async with self.get_session() as session:
                service = CommunicationService(session)
                tags = await service.get_available_tags()

            async with self:
                self.available_tags = tags
                if not self.selected_tag and self.available_tags:
                    self.selected_tag = self.available_tags[0]

            console.info(f"Loaded {len(self.available_tags)} tags")

            # Load initial data (call internal fetch without yield)
            await self._fetch_data()

        except Exception as e:
            console.error(f"Initialize failed: {e}")
            await self.set_error(str(e))
        finally:
            async with self:
                self.loading = False

    async def _fetch_data(self):
        """Internal data fetch without yield (for initialize)"""
        import time

        # Get current values
        selected_tag = self.selected_tag
        selected_days = self.selected_days

        start_time = time.time()
        console.info(f"[TIMING] Starting data fetch for tag={selected_tag}, days={selected_days}")

        try:
            t_session_start = time.time()
            async with self.get_session() as session:
                console.info(f"[TIMING] Session created: {time.time() - t_session_start:.3f}s")

                service = CommunicationService(session)

                # Fetch hourly data
                t1 = time.time()
                hourly = await service.get_hourly_stats(selected_tag, selected_days)
                hourly_time = time.time() - t1
                console.info(f"[TIMING] Hourly stats ({len(hourly)} records): {hourly_time:.3f}s")

                # Fetch daily data
                t2 = time.time()
                daily = await service.get_daily_stats(selected_days)
                daily_time = time.time() - t2
                console.info(f"[TIMING] Daily stats ({len(daily)} records): {daily_time:.3f}s")

                # Fetch summary
                t3 = time.time()
                summary = await service.get_tag_summary(selected_tag, selected_days)
                summary_time = time.time() - t3
                console.info(f"[TIMING] Summary stats: {summary_time:.3f}s")

            # Update state
            t_state_update = time.time()
            async with self:
                self._df_hourly = hourly
                self._df_daily = daily
                self._summary = summary
                self.loading = False
            console.info(f"[TIMING] State update: {time.time() - t_state_update:.3f}s")

            total_time = time.time() - start_time
            console.info(f"[TIMING] Total fetch time: {total_time:.3f}s (hourly={hourly_time:.3f}s, daily={daily_time:.3f}s, summary={summary_time:.3f}s)")

        except Exception as e:
            console.error(f"Fetch data failed: {e}")
            await self.set_error(str(e))
            async with self:
                self.loading = False

    @rx.event(background=True)
    async def refresh_data(self):
        """데이터 새로고침 (with yield for UI updates)"""
        # Get current values
        selected_tag = self.selected_tag
        selected_days = self.selected_days

        console.info(f"Refreshing data for tag={selected_tag}, days={selected_days}")

        async with self:
            self.loading = True

        try:
            async with self.get_session() as session:
                service = CommunicationService(session)

                # Fetch all data in parallel would be ideal, but sequential is safer
                hourly = await service.get_hourly_stats(selected_tag, selected_days)
                daily = await service.get_daily_stats(selected_days)
                summary = await service.get_tag_summary(selected_tag, selected_days)

            async with self:
                self._df_hourly = hourly
                self._df_daily = daily
                self._summary = summary
                self.loading = False
                yield  # Update UI

            console.info(f"Loaded {len(hourly)} hourly records, {len(daily)} daily records")

        except Exception as e:
            console.error(f"Refresh data failed: {e}")
            await self.set_error(str(e))
            async with self:
                self.loading = False

    @rx.event(background=True)
    async def set_selected_tag(self, tag: str):
        """태그 선택 및 데이터 갱신"""
        async with self:
            self.selected_tag = tag

        return CommunicationState.refresh_data

    @rx.event(background=True)
    async def set_selected_days_str(self, days: str | List[str]):
        """일수 선택 및 자동 새로고침"""
        # Segmented control returns string or list
        if isinstance(days, list):
            days = days[0] if days else "7"

        try:
            days_int = int(days)
        except (ValueError, TypeError):
            days_int = 7

        async with self:
            self.selected_days = days_int

        return CommunicationState.refresh_data