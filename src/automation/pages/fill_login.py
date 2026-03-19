from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        # self.username = "#user-name"
        self.username = "#user-name"
        self.password = "#password"
        self.login_b = "#login-button"

    def fill_form(self,username:str,password:str):
        self.page.fill(self.username, username)
        self.page.fill(self.password, password)
        
    def click_login(self):
        self.page.click(self.login_b)