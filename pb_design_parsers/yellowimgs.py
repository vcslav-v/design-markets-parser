import os
from datetime import datetime, timedelta
from time import sleep

from selenium.common.exceptions import TimeoutException
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


def parse(username, password):
    domain = 'yellowimages.com'
    iso_start_date = os.environ.get('YELLOWIMGS_START_DATE') or '2000-01-01'
    last_db_sale = db_tools.get_last_date_in_db(domain, username)
    start_date = datetime.fromisoformat(iso_start_date).date()
    check_date = start_date if start_date > last_db_sale else last_db_sale + timedelta(days=1)
    sale_data = []
    if check_date >= datetime.utcnow().date():
        return

    driver = browser.get()
    browser.set_cookies(driver, f'https://{domain}', username)
    driver.get('https://yellowimages.com/yin/sales-summary')
    try:
        WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_element(By.ID, 'stat_form')
            )
    except TimeoutException:
        login(driver, username, password)

    while check_date < datetime.utcnow().date():
        driver.get(
            f'https://yellowimages.com/yin/daily-sales?date={check_date.strftime("%B %d, %Y")}'
        )
        table = WebDriverWait(driver, timeout=120).until(
            lambda d: d.find_element(By.ID, 'stat')
        )
        product_name_elems = table.find_elements(By.XPATH, '//tbody/tr//a[@class="popdizz"]')
        for product_name_elem in product_name_elems:
            product_name = product_name_elem.text
            product_row_elem = table.find_elements(
                By.XPATH,
                f'//tbody/tr//a[contains(.,"{product_name}")]/../../td',
            )
            earnings = int(float(product_row_elem[-1].text)*100)
            sale_data.append((check_date, product_name, earnings))
        check_date += timedelta(days=1)

    browser.save_cookies(driver, domain, username)

    push_to_db(sale_data, username, domain)
