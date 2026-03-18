from playwright.sync_api import Page
from pages.checkout_page import CheckoutOverviewPage
from pages.cart_page import CartPage
from pages.fill_login import LoginPage
from pages.inventory_page import InventoryItemPage
from pages.user_credential import UserCredential
from log_setup.logger_setup import get_logger

logger = get_logger()


def test_add_under_20_and_validate_all(page: Page):
    """
    Test Case: Validate complete purchase flow for items priced under $20.
    """

    logger.info("Starting test: test_add_under_20_and_validate_all")

    """
    Perform login using valid credentials.
    """
    login_page = LoginPage(page)
    login_page.fill_form('performance_glitch_user', 'secret_sauce')
    login_page.click_login()

    logger.info("Login successful")

    inventory_page = InventoryItemPage(page)
    cart_page = CartPage(page)

    added_names = []
    added_descriptions = []
    added_prices = []

    """
    Fetch all items from the inventory page.
    """
    all_items = inventory_page.get_all_items()

    """
    Iterate through inventory items and add only those
    whose price is less than $20.
    """
    for item in all_items:

        price_text = inventory_page.get_item_price(item)
        price = float(price_text.replace("$", "").strip())

        if price < 20:

            description = inventory_page.get_item_description(item)

            inventory_page.click_add_to_cart_btn(item)

            added_names.append(item.strip())
            added_descriptions.append(description.strip())
            added_prices.append(price)

    logger.info(f"Expected Names: {added_names}")
    logger.info(f"Expected Descriptions: {added_descriptions}")
    logger.info(f"Expected Prices: {added_prices}")

    """
    Navigate to the cart page.
    """
    cart_page.click_cart_button()

    cart_names = cart_page.get_cart_names()
    cart_desc = cart_page.get_cart_desc()
    cart_prices = cart_page.get_cart_prices()

    logger.info(f"Cart Names: {cart_names}")
    logger.info(f"Cart Descriptions: {cart_desc}")
    logger.info(f"Cart Prices: {cart_prices}")

    """
    Validate that cart items match the items added from inventory.
    """
    assert cart_names == added_names
    assert cart_desc == added_descriptions
    assert cart_prices == added_prices

    logger.info("Cart items validated successfully")

    """
    Remove a specific item from the cart and update expected lists.
    """
    removed_item = "Sauce Labs Onesie"
    cart_page.click_remove_button(removed_item)

    if removed_item in added_names:
        index = added_names.index(removed_item)
        added_names.pop(index)
        added_descriptions.pop(index)
        added_prices.pop(index)

    updated_cart = cart_page.get_cart_names()

    logger.info(f"Cart after remove: {updated_cart}")

    assert updated_cart == added_names

    logger.info("Item removed successfully")

    """
    Proceed to checkout.
    """
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

    logger.info(f"Overview Names: {overview_names}")
    logger.info(f"Overview Descriptions: {overview_desc}")
    logger.info(f"Overview Prices: {overview_prices}")

    """
    Validate that checkout overview items match the cart items.
    """
    assert overview_names == added_names
    assert overview_desc == added_descriptions
    assert overview_prices == added_prices

    logger.info("Checkout overview items validated")

    """
    Validate subtotal and tax calculation.
    """
    subtotal = overview_page.matching_price()
    tax = overview_page.get_tax()

    logger.info(f"Subtotal from UI: {subtotal}")
    logger.info(f"Tax from UI: {tax}")

    expected_tax = subtotal * 0.08

    assert sum(overview_prices) == subtotal
    assert tax == round(expected_tax, 2)

    logger.info("Subtotal and tax matched")

    """
    Validate total price calculation.
    """
    total = overview_page.total_price()

    logger.info(f"Total from UI: {total}")

    assert total == subtotal + round(expected_tax, 2)

    logger.info("Total price matched")

    """
    Finish the order.
    """
    overview_page.finish_btn()

    logger.info("Order finished successfully")