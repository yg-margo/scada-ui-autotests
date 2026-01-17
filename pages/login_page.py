from playwright.sync_api import Page, Locator, expect


class LoginPage:
    """Page Object для страницы логина"""

    def __init__(self, page: Page):
        self.page = page
        self._username_input: Locator = page.get_by_test_id("username")
        self._password_input: Locator = page.get_by_test_id("password")
        self._login_button: Locator = page.get_by_test_id("login-button")
        # Семантические локаторы
        self._login_section: Locator = page.locator("#login-page")
        self._login_heading: Locator = page.get_by_role("heading", name="Login")

    @property
    def username_input(self) -> Locator:
        """Поле ввода имени пользователя"""
        return self._username_input

    @property
    def password_input(self) -> Locator:
        """Поле ввода пароля"""
        return self._password_input

    @property
    def login_button(self) -> Locator:
        """Кнопка входа"""
        return self._login_button

    def is_visible(self) -> bool:
        """Проверка, отображается ли страница логина"""
        return self._login_section.is_visible()

    def login(self, username: str, password: str) -> None:
        """Выполнение логина"""
        self._username_input.fill(username)
        self._password_input.fill(password)
        self._login_button.click()

    def assert_login_page_loaded(self) -> None:
        """Проверка, что страница логина корректно загружена"""
        expect(self._login_heading).to_be_visible()
        expect(self._username_input).to_be_visible()
        expect(self._password_input).to_be_visible()
        expect(self._login_button).to_be_enabled()
