from playwright.sync_api import Page
from src.automation.pages.fill_login import LoginPage
from src.automation.pages.inventory_page import InventoryItemPage
from src.automation.pages.cart_page import CartPage
from src.automation.log_setup.logger_setup import get_logger

logger = get_logger()


def test_add_items_under_20(page: Page):
    """
    Test Case: Items priced under $20 are added to the cart correctly.
    """
    
    logger.info("Starting test: test_add_items_under_20")

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

    logger.info(f"Added items: {added_names}")

    cart_page.click_cart_button()

    cart_names = cart_page.get_cart_names()
    cart_desc = cart_page.get_cart_desc()
    cart_prices = cart_page.get_cart_prices()

    assert cart_names == added_names
    assert cart_desc == added_descriptions
    assert cart_prices == added_prices

    logger.info("Inventory items under $20 validated in cart")
