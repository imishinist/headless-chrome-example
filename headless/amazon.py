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

    def __init__(self, driver):
        self.__driver = driver

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

    def __validate(self, email, password):
        if email is None or password is None:
            return False
        return True


def generate_driver():
    options = Options()
    options.headless = False
    options.incognito = True
    options.hide_scrollbars = True

    return webdriver.Chrome(options=options)


def main():
    amazon_email = os.environ.get('AMAZON_EMAIL')
    amazon_password = os.environ.get('AMAZON_PASSWORD')
    amazon_totp_secret = os.environ.get('AMAZON_TOTP_SECRET')

    driver = generate_driver()

    amazon = Amazon(driver)
    amazon.login(amazon_email, amazon_password, amazon_totp_secret)

    time.sleep(10)
    driver.close()


if __name__ == '__main__':
    main()
