from time import sleep
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import os

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from loguru import logger

from pb_design_parsers import browser, db_tools


def login(driver, username, password):
    input_username = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'inputEmail')
    )
    input_username.send_keys(username)
    input_pass = driver.find_element(By.ID, 'inputPassword')
    input_pass.send_keys(password)
    sleep(2)
    log_button = driver.find_element(By.ID, 'submLogin')
    log_button.click()

    WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'logoff')
    )


def get_logined_driver(username, password):
    driver = browser.get()
    browser.set_cookies(driver, 'https://designer.youworkforthem.com', username)
    driver.get('https://designer.youworkforthem.com/login')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'logoff')
            )
    except TimeoutException:
        login(driver, username, password)
    return driver


@logger.catch
def parse(username, email, password):
    domain = 'designer.youworkforthem.com'
    iso_start_date = os.environ.get('YWFT_START_DATE') or '2000-01-01'
    last_db_sale = db_tools.get_last_date_in_db(domain, username)
    start_date = datetime.fromisoformat(iso_start_date).date()
    start_date = start_date if start_date > last_db_sale else last_db_sale + timedelta(days=1)
    check_date = start_date + timedelta(days=1)
    sale_data = []
    if check_date >= datetime.utcnow().date():
        return
    driver = get_logined_driver(email, password)

    while check_date < datetime.utcnow().date():
        try:
            sale_data.extend(get_data(driver, check_date))
        except WebDriverException:
            push_to_db(sale_data, username, domain)
            sale_data = []
            driver = get_logined_driver()
            sale_data.extend(get_data(driver, check_date))

        check_date = check_date + timedelta(days=1)

    browser.save_cookies(driver, 'https://designer.youworkforthem.com', username)
    driver.close()

    push_to_db(sale_data, username, domain)


def push_to_db(sale_data, username, domain):
    for sale in sale_data:
        check_date, product_name, product_earning, price = sale
        db_tools.add_sale(
            date=check_date,
            price=price,
            earnings=product_earning,
            product=product_name,
            reffered=False,
            market_place_domain=domain,
            username=username,
        )


def get_data(driver, check_date):
    iso_date = check_date.isoformat()
    url = f'https://designer.youworkforthem.com/sales/{iso_date},{iso_date}'
    driver.get(url)

    result = []
    try:
        name_elems = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_elements(By.XPATH, '//div[@class="salesList"]//p/strong')
        )
    except TimeoutException:
        return []

    for name_elem in name_elems:
        product_name = name_elem.text
        cell_elems = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_elements(
                By.XPATH,
                f'//div[@class="salesList"]//p/strong[text()="{product_name}"]/../../../li'
            )
        )
        _, _, price_elem, quantity_elem, _, earnings_elem, _ = cell_elems
        price = price_elem.text
        price = int(float(price[1:]) * 100)
        quantity = int(quantity_elem.text)
        earning = earnings_elem.text
        earning = int(float(earning[1:]) * 100)

        product_earning = earning // quantity
        remainder = earning % quantity

        for _ in range(quantity):
            result.append((check_date, product_name, product_earning + remainder, price))
            remainder = 0

    return result


@logger.catch
def refresh_products(username, designer_uid):
    driver = browser.get()
    driver.get(
        '/'.join([
            'https://www.youworkforthem.com/designer',
            designer_uid,
            username,
        ])
    )

    pagination_elems = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_elements(By.XPATH, '//ol[@class="pagination"]/li/a')
    )

    page_links = []
    for pagination_elem in pagination_elems:
        page_links.append(pagination_elem.get_attribute('href'))

    page_links = set(page_links)

    product_links = []
    for page_link in page_links:
        driver.get(page_link)
        product_link_elems = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_elements(By.XPATH, '//a[@class="alinkproduct"]')
        )

        for product_link_elem in product_link_elems:
            product_links.append(urljoin(
                'https://www.youworkforthem.com',
                product_link_elem.get_attribute('href'),
            ))

    product_items = []
    for product_link in product_links:
        try:
            product_items.append(parse_product_info(driver, product_link))
        except WebDriverException:
            driver = browser.get()
            product_items.append(parse_product_info(driver, product_link))

    for product_item in product_items:
        db_tools.add_product_item('designer.youworkforthem.com', username, *product_item)


def parse_product_info(driver, product_link):
    logger.debug(product_link)
    is_live = True
    driver.get(product_link)

    name_elem = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_element(By.XPATH, '//h1')
    )
    product_name = name_elem.text

    price_elem = WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_element(By.XPATH, '//div[contains(@class, "productPrice")]/span')
    )
    price = price_elem.text
    price = int(float(price[1:]) * 100)
    item_license_prices = {'commercial': price, 'extended': 10000}

    categories = [urlparse(product_link).path.strip('/').split('/')[0]]

    category_element = driver.find_element(
        By.XPATH,
        '//div[@id="subNavHolder"]//a[@class="active-bold"]'
    )
    categories.append(category_element.text)

    return (product_name, product_link, is_live, categories, item_license_prices)
