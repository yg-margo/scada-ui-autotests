from playwright.sync_api import Page, Locator, expect
from typing import List


class DashboardPage:
    """Page Object для страницы Dashboard."""

    def __init__(self, page: Page):
        self.page = page

        self._dashboard_section: Locator = page.locator("#dashboard-page")
        self._sensors_table: Locator = page.get_by_test_id("sensors-table")
        self._sensors_rows: Locator = page.locator("#sensors-body tr")
        self._status_indicator: Locator = page.locator(".status")
        self._dashboard_heading: Locator = page.get_by_role("heading", name="Dashboard")

        self._sensor_values: Locator = page.get_by_test_id("sensor-value")
        self._sensor_timestamps: Locator = page.get_by_test_id("sensor-updated")

    @property
    def sensors_table(self) -> Locator:
        """Локатор таблицы датчиков"""
        return self._sensors_table

    @property
    def status_indicator(self) -> Locator:
        """Индикатор статуса соединения"""
        return self._status_indicator

    def is_visible(self) -> bool:
        """Проверка, отображается ли дашборд"""
        return self._dashboard_section.is_visible()

    def wait_for_dashboard(self, timeout: int = 5000) -> None:
        """Ожидание полной загрузки дашборда"""
        self._sensors_table.wait_for(state="visible", timeout=timeout)
        self._status_indicator.wait_for(state="visible", timeout=timeout)

    def get_sensors_count(self) -> int:
        """Получение количество отображаемых датчиков"""
        self._sensors_rows.first.wait_for(state="visible")
        return self._sensors_rows.count()

    def get_sensor_value(self, sensor_index: int = 0) -> str:
        """Получение значение датчика по индексу"""
        return self._sensor_values.nth(sensor_index).text_content()

    def get_all_sensor_values(self) -> List[str]:
        """Получение значения всех датчиков"""
        count = self._sensor_values.count()
        return [self._sensor_values.nth(i).text_content() for i in range(count)]

    def wait_for_value_change(
        self,
        initial_value: str,
        sensor_index: int = 0,
        timeout: int = 3000,
    ) -> None:
        """Ожидание изменения значения датчика относительно начального"""
        sensor_locator = self._sensor_values.nth(sensor_index)
        expect(sensor_locator).not_to_have_text(initial_value, timeout=timeout)

    def assert_dashboard_loaded(self) -> None:
        """Проверка, что дашборд корректно загружен"""
        expect(self._dashboard_heading).to_be_visible()
        expect(self._sensors_table).to_be_visible()
        expect(self._status_indicator).to_be_visible()
        expect(self._status_indicator).to_have_text("Connected")

    def assert_minimum_sensors(self, min_count: int = 1) -> None:
        """Проверка, что отображается минимум заданное количество датчиков"""
        actual_count = self.get_sensors_count()
        assert (
            actual_count >= min_count
        ), f"Ожидалось как минимум {min_count} датчиков, но найдено {actual_count}"
