from playwright.sync_api import Page


class InventoryItemPage:
    def __init__(self, page: Page):
        self.page = page

        self.img_link = "//img[@data-test='{!s}']"
        self.item_description = "//div[text()='{!s}']/parent::a/following-sibling::div"
        self.item_price = "//div[text()='{!s}']/ancestor::div[@class='inventory_item_name']/following-sibling::div/div"
        self.add_to_cart_btn = "//button[@data-test='add-to-cart-{!s}']"
        self.remove_from_cart_btn = "#remove-{!s}"
        self.get_all_items_name = "//div[@data-test='inventory-item-name']"

    def get_img_link(self, item_name: str):
        item_name = f"inventory-item-{'-'.join(item_name.lower().split())}-img"
        return self.page.locator(self.img_link.format(item_name)).get_attribute("src")

    def get_item_description(self, item_name: str):
        return self.page.locator(self.item_description.format(item_name)).inner_text()

    def get_item_price(self, item_name: str):
        return self.page.locator(self.item_price.format(item_name)).inner_text()

    def click_add_to_cart_btn(self, item_name: str):
        item_name = '-'.join(item_name.lower().split())
        self.page.click(self.add_to_cart_btn.format(item_name))
        self.page.wait_for_timeout(2000)

    def get_all_items(self):
        return self.page.locator(self.get_all_items_name).all_inner_texts()


    def click_remove_from_cart_btn(self, item_name: str):
        item_name = '-'.join(item_name.lower().split())
        self.page.click(self.remove_from_cart_btn.format(item_name))