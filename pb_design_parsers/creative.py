"""Creative market parser."""

import os
from time import sleep

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import browser
from pb_design_parsers import UPLOAD_DIR


def uploaded_files(prefix):
    for file_path in os.listdir(UPLOAD_DIR):
        if file_path.split('-')[0] == prefix:
            yield os.path.join(UPLOAD_DIR, file_path)
            os.remove(os.path.join(UPLOAD_DIR, file_path))


def login(driver, username):
    input_username = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//input[@name="username"]')
    )
    input_username.send_keys(username)
    input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')
    input_pass.send_keys(os.environ.get(f'CREATIVE_PASS_{username}'))
    sleep(1)
    log_button = driver.find_element(By.XPATH, '//form/button')
    log_button.click()
    WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'header-cart')
    )


def get_data_csv(driver):
    driver.get('https://creativemarket.com/account/dashboard/sales')

    export_button = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(
            By.XPATH, '//p[@class="export-text"]/a[contains(.,"Export as CSV")]'
        )
    )
    export_button.click()


def push_data_csv(driver):
    pass


def parse(username):
    driver = browser.get()
    browser.set_cookies('https://creativemarket.com', username)
    driver.get('https://creativemarket.com/sign-in')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'header-cart')
            )
    except TimeoutException:
        login(driver, username)
    get_data_csv(driver)
    browser.save_cookies(driver, 'https://creativemarket.com', username)
    push_data_csv(driver)

def add_data():
    pass
