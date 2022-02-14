import calendar
import email
import imaplib
import imp
import re
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from loguru import logger
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pb_design_parsers import browser, db_tools


@logger.catch
def parse(username, mail_username, mail_password, imap_server, folder):
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(mail_username, mail_password)
    mail.select(folder)
    _, uid_data = mail.uid('search', None, 'ALL')

    mails_bodies = []
    email_uids = uid_data[0].split()
    for email_uid in email_uids:
        result, data = mail.uid('fetch', email_uid, '(RFC822)')
        logger.debug(result)
        mails_bodies.append(data[0][1])

    email_messages = []
    for mails_body in mails_bodies:
        email_messages.append(email.message_from_bytes(mails_body))

    for email_uid in email_uids:
        mail.store(email_uid, '+FLAGS', '\\Deleted')

    soups = []
    for email_message in email_messages:
        for email_part in email_message.walk():
            content = email_part.get_payload(decode=True)
            if content:
                soups.append(BeautifulSoup(email_part.get_payload(decode=True), 'lxml'))
                break
    products = []
    for soup in soups:
        raw_date = re.search(r'(?<=Marketplace report for ).*(?=,)', soup.text).group(0)
        month, year = raw_date.split(' ')
        first_day_date = datetime.strptime(f'{year}-{month}-01', '%Y-%B-%d').date()
        _, last_month_day = calendar.monthrange(first_day_date.year, first_day_date.month)
        date = datetime.strptime(f'{year}-{month}-{last_month_day}', '%Y-%B-%d').date()
        rows = soup.find_all('tr')[1:-1]
        for row in rows:
            cells = row.find_all('td')
            cells = list(map(lambda x: x.span.text, cells))
            product_name, amount, _, _, earnings = cells
            amount = int(amount)
            earnings = int(float(earnings) * 100)
            products.append((date, product_name, amount, earnings))

    for product in products:
        date, product_name, amount, earnings = product
        earnings_per_sale = earnings // amount
        remainder = earnings % amount
        for _ in range(amount):
            db_tools.add_sale(
                date=date,
                earnings=earnings_per_sale + remainder,
                product=product_name,
                reffered=False,
                market_place_domain='designcuts.com',
                username=username,
            )
            remainder = 0


@logger.catch
def refresh_products(username):
    driver = browser.get()
    page_num = 1
    is_content_exist = True
    product_links = []

    while is_content_exist:
        driver.get(f'https://www.designcuts.com/vendor/{username}/page/{page_num}/')

        try:
            product_link_elems = WebDriverWait(driver, timeout=10).until(
                lambda d: d.find_elements(By.XPATH, '//a[@class="title"]')
            )
        except TimeoutException:
            is_content_exist = False
            product_link_elems = []

        for product_link_elem in product_link_elems:
            product_links.append(product_link_elem.get_attribute('href'))

        page_num += 1

    product_items = []
    for product_link in product_links:
        try:
            product_items.append(parse_product_info(driver, product_link))
        except WebDriverException:
            driver = browser.get()
            product_items.append(parse_product_info(driver, product_link))

    for product_item in product_items:
        db_tools.add_product_item('designcuts.com', username, *product_item)


def parse_product_info(driver, product_link):
    driver.get(product_link)
    product_name_elem = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//section[@id="product-hero"]//h1')
    )
    product_name = product_name_elem.text

    try:
        category_elem = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(
                By.XPATH,
                '//section[@id="product-hero"]//a[@class="category"]',
            )
        )
    except TimeoutException:
        categories = []
    else:
        category_link = category_elem.get_attribute('href')
        category_path = urlparse(category_link).path
        categories = category_path.strip('/').split('/')
        categories = categories[1:]

    return (product_name, categories)
