from playwright.sync_api import Page


class CheckoutOverviewPage:

    def __init__(self, page: Page):
        self.page = page
        self.item_names = ".inventory_item_name"
        self.item_desc = ".inventory_item_desc"
        self.item_prices = ".inventory_item_price"

    def get_names(self):
        return self.page.locator(self.item_names).all_text_contents()

    def get_desc(self):
        return self.page.locator(self.item_desc).all_text_contents()

    def get_prices(self):
        prices = self.page.locator(self.item_prices).all_text_contents()
        return [float(p.replace("$","").strip())for p in prices]

    def matching_price(self):
        text = self.page.locator(".summary_subtotal_label").inner_text()

        return float(text.split("$")[1])

    def get_tax(self):
        text = self.page.locator(".summary_tax_label").inner_text()
        return float(text.split("$")[1])
    def total_price(self):
        text = self.page.locator(".summary_total_label").inner_text()
        return float(text.split("$")[1])
    def finish_btn(self):
        self.page.locator("#finish").click()
        print(self.page.locator(".complete-header").inner_text())

