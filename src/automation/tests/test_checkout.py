from playwright.sync_api import Page
from src.automation.pages.fill_login import LoginPage
from src.automation.pages.inventory_page import InventoryItemPage
from src.automation.pages.cart_page import CartPage
from src.automation.pages.user_credential import UserCredential
from src.automation.pages.checkout_page import CheckoutOverviewPage
from src.automation.log_setup.logger_setup import get_logger

logger = get_logger()


def test_checkout_price_and_finish(page: Page):
    """
    Test Case: Checkout overview prices are correct and order can be finished.
    """
    
    logger.info("Starting test: test_checkout_price_and_finish")

    login_page = LoginPage(page)
    login_page.fill_form('performance_glitch_user', 'secret_sauce')
    login_page.click_login()

    inventory_page = InventoryItemPage(page)
    cart_page = CartPage(page)

    added_names = []
    added_descriptions = []
    added_prices = []

    all_items = inventory_page.get_all_items()

    for item in all_items:
        price_text = inventory_page.get_item_price(item)
        price = float(price_text.replace("$", "").strip())

        if price < 20:
            description = inventory_page.get_item_description(item)
            inventory_page.click_add_to_cart_btn(item)
            added_names.append(item.strip())
            added_descriptions.append(description.strip())
            added_prices.append(price)

    cart_page.click_cart_button()

    removed_item = "Sauce Labs Onesie"
    cart_page.click_remove_button(removed_item)

    if removed_item in added_names:
        index = added_names.index(removed_item)
        added_names.pop(index)
        added_descriptions.pop(index)
        added_prices.pop(index)

    cart_page.click_checking_out()
    logger.info("Clicked checkout button")

    users = UserCredential(page)
    users.user_data("Parna", "Bhattacharya", "712232")
    users.click_conti()
    logger.info("User information submitted")

    overview_page = CheckoutOverviewPage(page)

    overview_names = overview_page.get_names()
    overview_desc = overview_page.get_desc()
    overview_prices = overview_page.get_prices()

    assert overview_names == added_names
    assert overview_desc == added_descriptions
    assert overview_prices == added_prices
    logger.info("Checkout overview items validated")

    subtotal = overview_page.matching_price()
    tax = overview_page.get_tax()
    expected_tax = subtotal * 0.08

    assert sum(overview_prices) == subtotal
    assert tax == round(expected_tax, 2)
    logger.info("Subtotal and tax matched")

    total = overview_page.total_price()
    assert total == subtotal + round(expected_tax, 2)
    logger.info("Total price matched")

    overview_page.finish_btn()
    logger.info("Order finished successfully")
