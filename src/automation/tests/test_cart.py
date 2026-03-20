from playwright.sync_api import Page
from src.automation.pages.fill_login import LoginPage
from src.automation.pages.inventory_page import InventoryItemPage
from src.automation.pages.cart_page import CartPage
from src.automation.log_setup.logger_setup import get_logger

logger = get_logger()


def test_remove_item_from_cart(page: Page):
    """
    Test Case: An item can be removed from the cart successfully.
    """
    
    logger.info("Starting test: test_remove_item_from_cart")

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

    updated_cart = cart_page.get_cart_names()

    assert updated_cart == added_names

    logger.info("Item removed from cart successfully")
