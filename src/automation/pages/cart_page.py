from playwright.sync_api import Page

class CartPage:
    def __init__(self, page: Page):
        self.page = page
        self.checking_out = "id=checkout"

    def click_cart_button(self):
        self.page.click("#shopping_cart_container")

    def get_cart_names(self):
        return self.page.locator(".inventory_item_name").all_inner_texts()

    def get_cart_desc(self):
        return self.page.locator(".inventory_item_desc").all_inner_texts()

    def get_cart_prices(self):
        prices = self.page.locator(".inventory_item_price").all_inner_texts()
        return [float(i.replace("$", "").strip()) for i in prices]

    def click_remove_button(self, item_name: str):
        formatted_name = '-'.join(item_name.lower().split())
        self.page.click(f"#remove-{formatted_name}")

    def click_checking_out(self):
        self.page.click(self.checking_out)

