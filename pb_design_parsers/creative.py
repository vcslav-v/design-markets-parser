"""Creative market parser."""

import os
from time import sleep
import csv
from datetime import datetime

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
    driver.get('https://dm-parser.herokuapp.com/upload-data')
    try:
        input_file = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, '//input[@name="data_file"]')
        )
    except TimeoutError:
        driver.get('https://dm-parser.herokuapp.com/upload-data')
        input_file = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, '//input[@name="data_file"]')
        )
    input_file.send_keys('/home/selenium/Downloads/Creative Market Sales.csv')
    input_prefix = driver.find_element(By.XPATH, '//input[@name="prefix"]')
    input_prefix.send_keys(CM_PB_PREFIX.format(username=username))
    submit_button = driver.find_element(
        By.XPATH,
        '//input[@name="data_file"]/../button[@type="submit"]'
    )
    submit_button.click()


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


def add_data(username):
    today = datetime.utcnow().date()
    cm_domain = 'creativemarket.com'
    last_data_day = db_tools.get_last_date_in_db(cm_domain, username)
    paths = uploaded_files(CM_PB_PREFIX.format(username=username))

    for path in paths:
        with open(path, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)
            for row in reader:
                date, product, customer, price, earnings = row[0], row[2], row[3], row[4], row[5]
                date = datetime.fromisoformat(date).date()
                price = int(float(price.replace(',', '')) * 100)
                earnings = int(float(earnings.replace(',', '')) * 100)
                reffered = True if customer == 'Referred Customer' else False

                if last_data_day < date < today:
                    db_tools.add_sale(date, price, earnings, product, reffered, cm_domain, username)


def refresh_products(username, password):
    driver = browser.get()
    browser.set_cookies(driver, 'https://creativemarket.com', username)
    driver.get('https://creativemarket.com/sign-in')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'header-cart')
            )
    except TimeoutException:
        login(driver, username, password)
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
        break  # test
        if next_button.get_attribute('disabled'):
            is_next = False
        else:
            next_button.click()

    product_items = []
    for product_link in product_links:
        product_items.append(parse_product_info(driver, product_link))
        break  # test
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

    status_elem = driver.find_element(By.XPATH, '//span[@class="status-label"]')
    is_live = True if 'Live' in status_elem.text else False

    item_license_prices = {}
    try:
        modal_link_elem = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(
                By.XPATH,
                '//div[@class="license-section"]//a[contains(@class, "license-modal-link")]',
            )
        )
        modal_link_elem.click()
    except TimeoutException:
        license_title_elems = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_elements(
                By.XPATH,
                '//span[@class="license-title"]',
            )
        )

        for license_title_elem in license_title_elems:
            name_license = license_title_elem.text
            lic_div = f'//div[@class="license-section"]//span[contains(., "{name_license}")]/../..'
            price_elem = driver.find_element(
                By.XPATH,
                f'{lic_div}/div[@class="license-price"]',
            )
            price_license = price_elem.text
            price_license = int(float(price_license[1:]) * 100)
            item_license_prices[name_license] = price_license

    else:
        license_button_elems = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_elements(
                By.XPATH,
                '//div[@class="right"]/button[contains(@class, "license-button")]',
            )
        )

        for license_button_elem in license_button_elems:
            name_license = license_button_elem.get_attribute('data-tracking')
            license_button_path = f'//div[@class="right"]/button[@data-tracking="{name_license}"]'
            price_elem = driver.find_element(
                By.XPATH,
                f'{license_button_path}//span[contains(@class, "license-price")]',
            )
            price_license = price_elem.text
            price_license = int(float(price_license[1:]) * 100)
            item_license_prices[name_license] = price_license

    return (product_name, product_link, is_live, categories, item_license_prices)
