import pytest
from pathlib import Path
from playwright.sync_api import Page, Browser, BrowserContext


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Настройка параметров контекста браузера для всех тестов сессии"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "ru-RU",
    }


@pytest.fixture
def html_path():
    """Вернуть путь к HTML-файлу тестируемого интерфейса"""
    return Path(__file__).parent / "scada_ui.html"


@pytest.fixture
def page_with_routes(page: Page, html_path):
    """
    Фикстура страницы с настроенным перехватом API для стабильности тестов.

    Демонстрирует:
    — мокирование ответов API датчиков,
    — перехват и стабилизацию ответов логина,
    — устойчивые тесты даже при отсутствии реального бэкенда.
    """

    def handle_sensors_api(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=(
                '{"sensors": ['
                '{"id": "TEMP-1", "value": 20.5}, '
                '{"id": "PRESS-2", "value": 100.2}'
                "]}"

            ),
        )

    page.route("**/api/sensors", handle_sensors_api)
    page.route(
        "**/api/login",
        lambda route: route.fulfill(
            status=200,
            body='{"success": true, "token": "mock-token"}',
        ),
    )

    page.goto(f"file://{html_path.absolute()}")

    yield page


@pytest.fixture
def context_with_storage(browser: Browser, html_path):
    """
    Контекст браузера с заранее сохранённым состоянием
    для тестов, которым нужна предварительная авторизация.
    """
    context: BrowserContext = browser.new_context()
    page: Page = context.new_page()

    page.goto(f"file://{html_path.absolute()}")

    page.get_by_test_id("username").fill("operator")
    page.get_by_test_id("password").fill("password")
    page.get_by_test_id("login-button").click()

    page.get_by_test_id("sensors-table").wait_for(state="visible")

    storage = context.storage_state()
    context.close()

    new_context: BrowserContext = browser.new_context(storage_state=storage)
    yield new_context
    new_context.close()
