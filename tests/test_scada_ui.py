import re
import pytest
import allure
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


class TestScadaUI:
    """Набор UI-тестов для интерфейса SCADA-оператора."""

    @pytest.mark.smoke
    def test_01_successful_login(self, page_with_routes: Page):
        """
        Тест 1: Проверка успешного сценария логина.

        Шаги:
        1. Открыть страницу логина
        2. Ввести логин и пароль
        3. Нажать кнопку входа
        4. Убедиться, что пользователь авторизован и отображается дашборд
        """
        with allure.step("Инициализировать объекты страниц Login и Dashboard"):
            login_page = LoginPage(page_with_routes)
            dashboard_page = DashboardPage(page_with_routes)

        with allure.step("Проверить, что страница логина корректно загружена"):
            login_page.assert_login_page_loaded()

        with allure.step("Выполнить логин с корректными учётными данными"):
            login_page.login("operator", "securepassword")

        with allure.step("Дождаться загрузки дашборда и проверить, что он отображается"):
            dashboard_page.wait_for_dashboard()
            expect(login_page._login_section).to_be_hidden()
            expect(dashboard_page._dashboard_section).to_be_visible()
            dashboard_page.assert_dashboard_loaded()

    @pytest.mark.smoke
    def test_02_sensors_table_display(self, page_with_routes: Page):
        """
        Тест 2: Проверка отображения таблицы датчиков.

        Шаги:
        1. Выполнить логин
        2. Убедиться, что таблица датчиков отображается
        3. Убедиться, что в таблице есть как минимум один датчик
        """
        with allure.step("Инициализировать объекты страниц Login и Dashboard"):
            login_page = LoginPage(page_with_routes)
            dashboard_page = DashboardPage(page_with_routes)

        with allure.step("Выполнить логин"):
            login_page.login("operator", "password123")
            dashboard_page.wait_for_dashboard()

        with allure.step("Проверить, что таблица датчиков отображается"):
            expect(dashboard_page.sensors_table).to_be_visible()

        with allure.step("Проверить, что в таблице есть минимум один датчик"):
            dashboard_page.assert_minimum_sensors(min_count=1)

        with allure.step("Проверить структуру таблицы и наличие данных по датчику"):
            sensors_count = dashboard_page.get_sensors_count()
            assert sensors_count >= 1, "Ожидался как минимум 1 датчик в таблице"

            first_sensor_value = dashboard_page.get_sensor_value(0)
            assert first_sensor_value is not None, "Значение датчика не должно быть None"
            assert len(first_sensor_value) > 0, "Значение датчика не должно быть пустым"

    @pytest.mark.regression
    def test_03_sensor_values_update(self, page_with_routes: Page):
        """
        Тест 3: Проверка обновления значений датчиков со временем.

        Шаги:
        1. Выполнить логин
        2. Считать начальное значение датчика
        3. Подождать изменения значения
        4. Убедиться, что значение изменилось (без проверки конкретного числа)
        """
        with allure.step("Инициализировать объекты страниц Login и Dashboard"):
            login_page = LoginPage(page_with_routes)
            dashboard_page = DashboardPage(page_with_routes)

        with allure.step("Выполнить логин и дождаться загрузки дашборда"):
            login_page.login("admin", "admin123")
            dashboard_page.wait_for_dashboard()

        with allure.step("Считать начальное значение первого датчика"):
            initial_value = dashboard_page.get_sensor_value(0)
            assert initial_value is not None, "Начальное значение датчика должно быть задано"

        with allure.step("Дождаться изменения значения первого датчика"):
            dashboard_page.wait_for_value_change(
                initial_value,
                sensor_index=0,
                timeout=3000,
            )

        with allure.step("Проверить, что значение первого датчика действительно изменилось"):
            updated_value = dashboard_page.get_sensor_value(0)
            assert updated_value != initial_value, (
                f"Значение датчика должно измениться относительно {initial_value}"
            )

        with allure.step("Проверить, что меняются значения датчиков не только у одного сенсора"):
            initial_values = dashboard_page.get_all_sensor_values()
            page_with_routes.wait_for_timeout(1500)
            updated_values = dashboard_page.get_all_sensor_values()

            changes_detected = any(
                initial != updated
                for initial, updated in zip(initial_values, updated_values)
            )
            assert (
                changes_detected
            ), "Минимум одно значение датчика должно измениться за время ожидания"

    @pytest.mark.api
    def test_04_network_response_and_api_interception(self, page: Page, html_path):
        """
        Тест 4: Проверка сетевых ответов и перехвата API-запросов (route/fulfill).

        Шаги:
        1. Настроить перехват запросов **/api/login и **/api/sensors и вернуть тестовые JSON ответы (fulfill).
        2. Подписаться на событие page.on("response") для сбора сетевых ответов.
        3. Открыть локальный HTML (file://...) и дождаться ответа на документ scada_ui.html через expect_response.
        4. Выполнить логин через UI и дождаться загрузки Dashboard, убедиться, что есть данные по датчикам.
        5. Отдельно триггернуть fetch-запросы к /api/login и /api/sensors и дождаться ответов через expect_response.
        6. Проверить, что перехват сработал (в intercepted_requests есть "login" и "sensors").
        7. Проверить, что среди полученных network responses есть ответ для scada_ui.html.
        """
        intercepted_requests = []
        responses_received = []

        def fulfill_json(route, body: str):
            route.fulfill(
                status=200,
                content_type="application/json",
                headers={"access-control-allow-origin": "*"},
                body=body,
            )

        with allure.step("Настроить перехват /api/login и /api/sensors"):
            def handle_api_login(route):
                intercepted_requests.append("login")
                fulfill_json(route, '{"success": true, "sessionId": "test-session-123"}')

            def handle_api_sensors(route):
                intercepted_requests.append("sensors")
                fulfill_json(
                    route,
                    '{"sensors":[{"id":"TEMP-1","value":25.5},{"id":"PRESS-2","value":101.3}]}',
                )

            page.route("**/api/login", handle_api_login)
            page.route("**/api/sensors", handle_api_sensors)

        with allure.step("Подписаться на ответы сети"):
            page.on("response", lambda r: responses_received.append({"url": r.url, "status": r.status}))

        with allure.step("Открыть HTML и ДОЖДАТЬСЯ network-response на документ"):
            with page.expect_response(re.compile(r".*scada_ui\.html$")) as resp_info:
                page.goto(f"file://{html_path.absolute()}")
            doc_resp = resp_info.value
            assert doc_resp.ok, f"Документ не загрузился, status={doc_resp.status}"

        with allure.step("Выполнить логин (UI часть) и дождаться Dashboard"):
            login_page = LoginPage(page)
            dashboard_page = DashboardPage(page)
            login_page.assert_login_page_loaded()
            login_page.login("test_user", "test_password")
            dashboard_page.wait_for_dashboard(timeout=5000)
            dashboard_page.assert_minimum_sensors(min_count=1)

        with allure.step("Демонстрация API interception: триггерим запросы и ждём responses"):
            with page.expect_response("**/api/login") as login_resp_info:
                login_json = page.evaluate(
                    """async () => {
                        const r = await fetch('https://mock.local/api/login', { method: 'POST' });
                        return await r.json();
                    }"""
                )
            assert login_resp_info.value.ok
            assert login_json["success"] is True
            with page.expect_response("**/api/sensors") as sensors_resp_info:
                sensors_json = page.evaluate(
                    """async () => {
                        const r = await fetch('https://mock.local/api/sensors');
                        return await r.json();
                    }"""
                )
            assert sensors_resp_info.value.ok
            assert "sensors" in sensors_json
            assert len(sensors_json["sensors"]) >= 1
        with allure.step("Проверить, что перехваты реально сработали"):
            assert "login" in intercepted_requests, "Не был перехвачен /api/login"
            assert "sensors" in intercepted_requests, "Не был перехвачен /api/sensors"
        with allure.step("Проверить, что были сетевые ответы (минимум документ)"):
            assert any("scada_ui.html" in r["url"] for r in responses_received), \
                "В логах ответов нет scada_ui.html"
