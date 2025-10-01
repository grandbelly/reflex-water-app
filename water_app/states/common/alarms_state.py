"""
Alarms State - Unified rule-based alarm management
- Uses AlarmService with proper connection pool
- Direct rx.State inheritance (no BaseState)
- Background events for async operations
"""
import reflex as rx
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from reflex.utils import console

from water_app.db_orm import get_async_session
from water_app.services.alarm_service import AlarmService


class AlarmsState(rx.State):
    """Unified alarm state for RULE_BASE alarms"""

    # Data storage
    alarms: List[Dict] = []
    statistics: Dict[str, Any] = {
        "total": 0,
        "critical": 0,
        "warning": 0,
        "info": 0,
        "unacknowledged": 0
    }

    # UI control
    loading: bool = False
    error_message: str = ""
    last_update: str = ""

    # Filters
    selected_hours: int = 168  # 7 days default (was 24)
    show_acknowledged: bool = False

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
    def filtered_alarms(self) -> List[Dict]:
        """Filter alarms based on show_acknowledged"""
        if self.show_acknowledged:
            return self.alarms
        return [a for a in self.alarms if not a.get("acknowledged", False)]

    @rx.var
    def critical_alarms(self) -> List[Dict]:
        """Get critical level alarms only"""
        return [a for a in self.filtered_alarms if a.get("level") == 5]

    @rx.var
    def warning_alarms(self) -> List[Dict]:
        """Get warning level alarms only"""
        return [a for a in self.filtered_alarms if a.get("level") == 3]

    # Event Handlers
    # =========================================================================

    @rx.event(background=True)
    async def initialize(self):
        """Initialize - load data on mount"""
        console.info("AlarmsState.initialize() called")

        async with self:
            self.loading = True

        try:
            await self._fetch_data()

        except Exception as e:
            console.error(f"Initialize failed: {e}")
            await self.set_error(str(e))
        finally:
            async with self:
                self.loading = False

    async def _fetch_data(self):
        """Internal data fetch without yield (for initialize)"""
        selected_hours = self.selected_hours

        console.info(f"Fetching alarms for last {selected_hours} hours")

        try:
            async with self.get_session() as session:
                service = AlarmService(session)

                # Fetch alarms and statistics
                alarms = await service.get_rule_based_alarms(hours=selected_hours)
                stats = await service.get_alarm_statistics(hours=selected_hours)

            async with self:
                self.alarms = alarms
                self.statistics = stats
                self.last_update = "Just now"
                self.loading = False

            console.info(f"Loaded {len(alarms)} alarms, {stats['critical']} critical")

        except Exception as e:
            console.error(f"Fetch data failed: {e}")
            await self.set_error(str(e))
            async with self:
                self.loading = False

    @rx.event(background=True)
    async def refresh_data(self):
        """Refresh alarm data (with yield for UI updates)"""
        console.info("Refreshing alarm data")

        async with self:
            self.loading = True

        try:
            await self._fetch_data()

            async with self:
                yield  # Update UI

        except Exception as e:
            console.error(f"Refresh failed: {e}")
            await self.set_error(str(e))
            async with self:
                self.loading = False

    @rx.event(background=True)
    async def set_hours_filter(self, hours):
        """Change hour filter and refresh"""
        # Handle both string and list from segmented_control
        if isinstance(hours, list):
            hours_int = int(hours[0]) if hours else 24
        else:
            hours_int = int(hours) if hours else 24

        async with self:
            self.selected_hours = hours_int

        return AlarmsState.refresh_data

    @rx.event
    def toggle_show_acknowledged(self):
        """Toggle show acknowledged alarms"""
        self.show_acknowledged = not self.show_acknowledged

    @rx.event(background=True)
    async def acknowledge_alarm(self, event_id: str):
        """Acknowledge an alarm"""
        console.info(f"Acknowledging alarm: {event_id}")

        try:
            async with self.get_session() as session:
                service = AlarmService(session)
                success = await service.acknowledge_alarm(event_id, "user")

            if success:
                # Update local state
                async with self:
                    for alarm in self.alarms:
                        if alarm.get("event_id") == event_id:
                            alarm["acknowledged"] = True
                            alarm["acknowledged_by"] = "user"
                            break
                    yield  # Update UI

                console.info(f"Successfully acknowledged alarm {event_id}")
            else:
                console.error(f"Failed to acknowledge alarm {event_id}")

        except Exception as e:
            console.error(f"Acknowledge alarm failed: {e}")
            await self.set_error(str(e))