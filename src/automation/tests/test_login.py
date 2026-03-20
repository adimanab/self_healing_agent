from playwright.sync_api import Page
from src.automation.pages.fill_login import LoginPage
from src.automation.log_setup.logger_setup import get_logger

logger = get_logger()


def test_login(page: Page):
    """
    Test Case: User can log in with valid credentials.
    """
    
    logger.info("Starting test: test_login")

    login_page = LoginPage(page)
    login_page.fill_form('performance_glitch_user', 'secret_sauce')
    login_page.click_login()

    logger.info("Login successful")
