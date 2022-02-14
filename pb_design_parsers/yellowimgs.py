import os
from datetime import datetime, timedelta
from time import sleep
from loguru import logger

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pb_design_parsers import browser, db_tools


def login(driver, username, password):
    input_username = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//input[@name="login_name"]')
    )
    input_username.send_keys(username)
    input_pass = driver.find_element(By.XPATH, '//input[@name="login_password"]')
    input_pass.send_keys(password)
    sleep(2)
    log_button = driver.find_element(By.ID, 'wbb-submit')
    log_button.click()
    WebDriverWait(driver, timeout=120).until(
        lambda d: d.find_element(By.ID, 'stat_form')
    )


def push_to_db(sale_data, username, domain):
    for sale in sale_data:
        check_date, product_name, earnings = sale
        db_tools.add_sale(
            date=check_date,
            earnings=earnings,
            product=product_name,
            reffered=False,
            market_place_domain=domain,
            username=username,
        )


def get_logined_driver(username, password):
    driver = browser.get()
    browser.set_cookies(driver, 'https://yellowimages.com', username)
    driver.get('https://yellowimages.com/yin/sales-summary')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'stat_form')
            )
    except TimeoutException:
        login(driver, username, password)
    return driver


@logger.catch
def parse(username, password):
    domain = 'yellowimages.com'
    iso_start_date = os.environ.get('YELLOWIMGS_START_DATE') or '2000-01-01'
    last_db_sale = db_tools.get_last_date_in_db(domain, username)
    start_date = datetime.fromisoformat(iso_start_date).date()
    check_date = start_date if start_date > last_db_sale else last_db_sale + timedelta(days=1)
    month_number = check_date.month
    sale_data = []
    if check_date >= datetime.utcnow().date():
        return

    driver = get_logined_driver(username, password)
    while check_date < datetime.utcnow().date():
        if month_number != check_date.month:
            browser.save_cookies(driver, 'https://yellowimages.com', username)
            driver.close()
            driver = get_logined_driver(username, password)
            month_number = check_date.month
            push_to_db(sale_data, username, domain)
            sale_data = []
        date_request = check_date.strftime("%B %d, %Y")
        driver.get(
            f'https://yellowimages.com/yin/daily-sales?date={date_request}'
        )
        try:
            table = WebDriverWait(driver, timeout=120).until(
                lambda d: d.find_element(By.ID, 'stat')
            )
        except TimeoutException:
            break
        product_name_elems = table.find_elements(By.XPATH, '//tbody/tr//a[@class="popdizz"]')
        for product_name_elem in product_name_elems:
            product_name = product_name_elem.text
            product_row_elem = table.find_elements(
                By.XPATH,
                f'//tbody/tr//a[contains(.,"{product_name}")]/../../td',
            )
            text_earning = product_row_elem[-1].text
            try:
                earnings = int(float(text_earning)*100)
            except ValueError:
                product_row_elem = table.find_elements(
                    By.XPATH,
                    f'//tbody/tr//a[contains(.,"{product_name}")]/../../td/span',
                )
                text_earning = product_row_elem[-1].text
                earnings = int(float(text_earning)*100)
            sale_data.append((check_date, product_name, earnings))
        check_date += timedelta(days=1)

    browser.save_cookies(driver, 'https://yellowimages.com', username)
    driver.close()

    push_to_db(sale_data, username, domain)


@logger.catch
def refresh_products(username, password):
    driver = get_logined_driver(username, password)
    base_caregories = ['objects', 'store', '3d-models', 'creative-fonts']
    product_links = []
    draft_product_links = []

    for base_caregory in base_caregories:
        items_exist = True
        page_number = 1
        while items_exist:
            driver.get(f'https://yellowimages.com/yin/products/{base_caregory}?page={page_number}')
            sleep(2)
            try:
                product_link_elems = WebDriverWait(driver, timeout=10).until(
                    lambda d: d.find_elements(By.XPATH, '//li[contains(@class, "post_item")]//h3/a')
                )
            except TimeoutException:
                items_exist = False
                product_link_elems = []
            for product_link_elem in product_link_elems:
                product_links.append(product_link_elem.get_attribute('href'))
            page_number += 1

        items_exist = True
        page_number = 1
        while items_exist:
            driver.get(
                f'https://yellowimages.com/yin/products/{base_caregory}/draft?page={page_number}'
            )
            sleep(2)
            try:
                product_link_elems = WebDriverWait(driver, timeout=10).until(
                    lambda d: d.find_elements(By.XPATH, '//li[contains(@class, "post_item")]//h3/a')
                )
            except TimeoutException:
                items_exist = False
                product_link_elems = []
            for product_link_elem in product_link_elems:
                draft_product_links.append(product_link_elem.get_attribute('href'))
            page_number += 1

    product_items = []
    for product_link in product_links:
        try:
            product_items.append(parse_product_info(driver, product_link, True))
        except WebDriverException:
            push_db(username, product_items)
            product_items = []
            sleep(30)
            driver = get_logined_driver(username, password)
            product_items.append(parse_product_info(driver, product_link, True))

    for product_link in draft_product_links:
        try:
            product_items.append(parse_product_info(driver, product_link, False))
        except WebDriverException:
            push_db(username, product_items)
            product_items = []
            sleep(30)
            driver = get_logined_driver(username, password)
            product_items.append(parse_product_info(driver, product_link, True))


def push_db(username, product_items):
    for product_item in product_items:
        db_tools.add_product_item('yellowimages.com', username, *product_item)


def parse_product_info(driver, product_link):
    driver.get(product_link)
    name_elem = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_element(
            By.XPATH,
            '//h2[@itemprop="name"]',
        )
    )
    product_name = name_elem.text
    category_elems = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_elements(
            By.XPATH,
            '//a[@class="fcat"]',
        )
    )
    categories = []
    for category_elem in category_elems:
        category_name = category_elem.text
        categories.append(category_name.lower())

    return (product_name, categories)
