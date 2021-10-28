import calendar
import os
from datetime import datetime, timedelta
from time import sleep

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pb_design_parsers import browser, db_tools


def login(driver, username, password):
    input_username = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//input[@name="username"]')
    )
    input_username.send_keys(username)
    input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')
    input_pass.send_keys(password)
    sleep(2)
    log_button = driver.find_element(By.XPATH, '//form/button')
    log_button.click()

    WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//a[@href="/sign-out"]')
    )


def get_data(driver, check_date):
    url = 'https://elements-contributors.envato.com/account/earnings/{iso_date}'
    driver.get(url.format(iso_date=check_date.isoformat()[:-3]))

    result = []
    while True:
        WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, '//h3[contains(., "Earnings By Items")]')
        )
        try:
            table = WebDriverWait(driver, timeout=20).until(
                lambda d: d.find_element(By.XPATH, '//tbody[@class="reactable-data"]/tr')
            )
        except TimeoutException:
            break
        for row in table:
            product_name = row.find_element(By.XPATH, 'td[@label="Item"]').text
            product_earning = row.find_element(By.XPATH, 'td[@label="Earnings (USD)"]').text
            product_earning = int(float(product_earning[1:])*100)
            result.append((check_date, product_name, product_earning))

        try:
            next_button = WebDriverWait(driver, timeout=20).until(
                lambda d: d.find_element(By.XPATH, '//a[@class="reactable-next-page"]')
            )
            next_button.click()
        except TimeoutException:
            break

    return result


def push_to_db(sale_data, username, domain):
    for sale in sale_data:
        check_date, product_name, product_earning = sale
        db_tools.add_sale(
            date=check_date,
            earnings=product_earning,
            product=product_name,
            reffered=False,
            market_place_domain=domain,
            username=username,
        )


def parse(username, password):
    driver = browser.get()
    domain = 'elements-contributors.envato.com'
    browser.set_cookies(driver, 'https://elements-contributors.envato.com', username)
    driver.get('https://elements-contributors.envato.com/sign-in')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'IconUserCircleTitle')
            )
    except TimeoutException:
        login(driver, username, password)

    iso_start_date = os.environ.get('ENVANTO_START_DATE') or '2000-01-01'
    last_db_sale = db_tools.get_last_date_in_db(domain, username)
    start_date = datetime.fromisoformat(iso_start_date).date()
    start_date = start_date if start_date > last_db_sale else last_db_sale + timedelta(days=1)
    _, last_month_day = calendar.monthrange(start_date.year, start_date.month)
    check_date = start_date + timedelta(days=last_month_day-1)
    sale_data = []
    while check_date < datetime.utcnow().date():
        sale_data.extend(get_data(driver, check_date))

        temp_date = check_date + timedelta(days=1)
        _, last_month_day = calendar.monthrange(temp_date.year, temp_date.month)
        check_date = temp_date + timedelta(days=last_month_day-1)
    browser.save_cookies(driver, 'https://elements-contributors.envato.com', username)

    push_to_db(sale_data, username, domain)
