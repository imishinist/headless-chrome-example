import json
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import pyotp


class Amazon:
    LOGIN_URL = "https://www.amazon.co.jp/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww" \
                ".amazon.co.jp%2F%3Fref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth" \
                "%2F2.0%2Fidentifier_select&openid.assoc_handle=jpflex&openid.mode=checkid_setup&openid.claimed_id" \
                "=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid" \
                ".net%2Fauth%2F2.0& "
    ORDER_HISTORY_URL = "https://www.amazon.co.jp/gp/css/order-history"

    def __init__(self, driver: webdriver.Chrome):
        self.__driver = driver

    def index(self):
        self.__driver.get('https://www.amazon.co.jp/')

    def login(self, email, password, totp_secret):
        totp = pyotp.TOTP(totp_secret)

        if not self.__validate(email, password):
            return False

        self.__driver.get(self.LOGIN_URL)
        self.__driver.find_element(By.ID, 'ap_email').send_keys(email)
        self.__driver.find_element(By.ID, 'continue').submit()

        self.__driver.find_element(By.ID, 'ap_password').send_keys(password)
        self.__driver.find_element(By.ID, 'signInSubmit').submit()

        try:
            wait = WebDriverWait(self.__driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "auth-mfa-otpcode")))
        except TimeoutException:
            return False

        self.__driver.find_element(By.ID, 'auth-mfa-otpcode').send_keys(totp.now())
        self.__driver.find_element(By.ID, 'auth-signin-button').submit()
        return True

    def orders(self):
        self.__driver.get(self.ORDER_HISTORY_URL)

        i = 0
        elements = self.__driver.find_elements(By.CLASS_NAME, 'hide-if-no-js')
        for element in elements:
            i += 1
            element.click()
            try:
                self.__driver.implicitly_wait(3)
                content = self.__driver.find_element(By.ID, 'a-popover-content-{}'.format(i))
                self.__driver.implicitly_wait(3)
                content.find_element(By.CLASS_NAME, 'a-link-normal')
            except TimeoutException:
                return False

        links = []
        elements = self.__driver.find_elements(By.CLASS_NAME, 'a-popover-content')
        for element in elements:
            link = element.find_elements(By.CLASS_NAME, 'a-link-normal')
            if len(link) == 0:
                continue
            payment_link = link[-1].get_attribute('href')
            links.append(payment_link)

        for (idx, link) in enumerate(links):
            self.__driver.get(link)
            try:
                wait = WebDriverWait(self.__driver, 10)
                wait.until(EC.presence_of_all_elements_located)
                self.__driver.execute_script("document.title = \'{}.pdf\'".format(idx+1))
                self.__driver.execute_script('window.print()')
            except TimeoutException:
                return False

    @staticmethod
    def __validate(email, password):
        if email is None or password is None:
            return False
        return True

    def save_cookies(self, file_name: str):
        with open(file_name, 'w') as f:
            json.dump(self.__driver.get_cookies(), f)

    """
    load_cookies を呼ぶ前に、一度サイトにアクセスしている必要がある
    """
    def load_cookies(self, file_name: str):
        with open(file_name) as f:
            cookies = json.load(f)

        for cookie in cookies:
            self.__driver.add_cookie(cookie)


def generate_driver(download_dir: str):
    options = Options()
    options.headless = False
    options.incognito = True
    options.hide_scrollbars = True
    appState = {
        "recentDestinations": [
            {
                "id": "Save as PDF",
                "origin": "local",
                "account": ""
            }
        ],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
        "pageSize": 'A4'
    }
    options.add_experimental_option("prefs", {
        "printing.print_preview_sticky_settings.appState":
            json.dumps(appState),
        "savefile.default_directory": download_dir
    })
    options.add_argument('--kiosk-printing')

    return webdriver.Chrome(options=options)


def main():
    amazon_email = os.environ.get('AMAZON_EMAIL')
    amazon_password = os.environ.get('AMAZON_PASSWORD')
    amazon_totp_secret = os.environ.get('AMAZON_TOTP_SECRET')


    import sys
    download_dir = 'downloads'
    download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../' + download_dir))
    print(download_dir)
    driver = generate_driver(download_dir + '/')

    amazon = Amazon(driver)
    amazon.login(amazon_email, amazon_password, amazon_totp_secret)

    amazon.orders()

    time.sleep(2)
    driver.close()


if __name__ == '__main__':
    main()
