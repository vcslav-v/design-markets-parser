"""Creative market parser."""

import os
from time import sleep
import csv
from datetime import datetime
from loguru import logger

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pb_design_parsers import browser, db_tools
from pb_design_parsers import UPLOAD_DIR, CM_PB_PREFIX, SPLITTER


def uploaded_files(prefix):
    for file_path in os.listdir(UPLOAD_DIR):
        if file_path.split(SPLITTER)[0] == prefix:
            yield os.path.join(UPLOAD_DIR, file_path)
            os.remove(os.path.join(UPLOAD_DIR, file_path))


def login(driver, username, password):
    input_username = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//input[@name="username"]')
    )
    input_username.send_keys(username)
    input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')
    input_pass.send_keys(password)
    sleep(1)
    log_button = driver.find_element(By.XPATH, '//form/button')
    log_button.click()
    WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'header-cart')
    )


def get_data_csv(driver):
    driver.get('https://creativemarket.com/account/dashboard/sales')

    try:
        dialog_dismiss_btn = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(
                By.XPATH, '//dialog//a[contains(@class, "dismiss")]'
            )
        )
        dialog_dismiss_btn.click()
    except TimeoutError:
        pass

    export_button = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(
            By.XPATH, '//p[@class="export-text"]/a[contains(.,"Export as CSV")]'
        )
    )
    export_button.click()


def push_data_csv(driver, username):
    driver.get(os.environ.get('SELF_POST_FILE_FORM'))
    try:
        try_btn = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, '//button[@class="btn try-out__btn"]')
        )
    except TimeoutError:
        driver.get(os.environ.get('SELF_POST_FILE_FORM'))
        try_btn = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, '//button[@class="btn try-out__btn"]')
        )
    try_btn.click()
    input_file = driver.find_element(By.XPATH, '//input[@type="file"]')
    input_file.send_keys('/home/selenium/Downloads/Creative Market Sales.csv')
    input_prefix = driver.find_element(By.XPATH, '//input[@placeholder="prefix"]')
    input_prefix.send_keys(CM_PB_PREFIX.format(username=username))
    submit_button = driver.find_element(
        By.XPATH,
        "//button[contains(.,'Execute')]"
    )
    submit_button.click()


@logger.catch
def parse(username, password):
    driver = browser.get()
    browser.set_cookies(driver, 'https://creativemarket.com', username)
    driver.get('https://creativemarket.com/sign-in')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'header-cart')
            )
    except TimeoutException:
        login(driver, username, password)
    get_data_csv(driver)
    browser.save_cookies(driver, 'https://creativemarket.com', username)
    push_data_csv(driver, username)


def add_data(username, file):
    today = datetime.utcnow().date()
    cm_domain = 'creativemarket.com'
    last_data_day = db_tools.get_last_date_in_db(cm_domain, username)
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        date, product, customer, price, earnings = row[0], row[2], row[3], row[4], row[5]
        date = datetime.fromisoformat(date).date()
        price = int(float(price.replace(',', '')) * 100)
        earnings = int(float(earnings.replace(',', '')) * 100)
        reffered = True if customer == 'Referred Customer' else False
        if last_data_day < date < today:
            db_tools.add_sale(date, price, earnings, product, reffered, cm_domain, username)


def get_logined_driver(username, password):
    driver = browser.get()
    browser.set_cookies(driver, 'https://creativemarket.com', username)
    driver.get('https://creativemarket.com/sign-in')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'header-cart')
            )
    except TimeoutException:
        login(driver, username, password)
    return driver


@logger.catch
def refresh_products(username, password):
    driver = get_logined_driver(username, password)
    driver.get('https://creativemarket.com/account/dashboard/products')
    try:
        dialog_dismiss_btn = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(
                By.XPATH, '//dialog//a[contains(@class, "dismiss")]'
            )
        )
        dialog_dismiss_btn.click()
    except TimeoutException:
        pass
    product_links = []
    is_next = True
    while is_next:
        sleep(5)
        product_elems = WebDriverWait(driver, timeout=10).until(
                    lambda d: d.find_elements(
                        By.XPATH,
                        '//section[@class="products box"]//tbody//tr/td[@class="product"]/a',
                    )
                )
        next_button = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(
                By.XPATH,
                '//nav[@class="pager"]/button[contains(.,"Next")]',
            )
        )
        for product_elem in product_elems:
            product_links.append(product_elem.get_attribute('href'))
        if next_button.get_attribute('disabled'):
            is_next = False
        else:
            next_button.click()

    product_items = []
    for i, product_link in enumerate(product_links):
        if i % 50 == 0:
            browser.save_cookies(driver, 'https://creativemarket.com', username)
            driver.close()
            driver = get_logined_driver(username, password)
        product_items.append(parse_product_info(driver, product_link))

    browser.save_cookies(driver, 'https://creativemarket.com', username)
    driver.close()

    for product_item in product_items:
        db_tools.add_product_item('creativemarket.com', username, *product_item)


def parse_product_info(driver, product_link):
    driver.get(product_link)
    name_elem = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_element(
            By.XPATH,
            '//div[@class="product-info"]/h1',
        )
    )
    product_name = name_elem.text

    breadcrumb_elems = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_elements(
            By.XPATH,
            '//div[contains(@class, "header-breadcrumbs")]/a',
        )
    )
    categories = []
    for breadcrumb_elem in breadcrumb_elems:
        category_name = breadcrumb_elem.text
        categories.append(category_name.lower())


    return (product_name, categories)
