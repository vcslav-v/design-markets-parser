import os

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from pb_design_parsers import (creative, designcuts, envanto, yellowimgs,
                               youworkforthem)

sched = BlockingScheduler()


def send_tg_alarm(message):
    requests.post(
            'https://api.telegram.org/bot{token}/sendMessage?chat_id={tui}&text={text}'.format(
                token=os.environ.get('ALLERT_BOT_TOKEN'),
                tui=os.environ.get('ADMIN_TUI'),
                text=message,
            ))


@sched.scheduled_job('cron', hour=19, minute=0)
@logger.catch
def parse_markets():
    logger.info('Start parsing sales')
    # try:
    #     creative.parse(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))
    # except Exception as e:
    #     logger.error(e)

    # try:
    #     creative.parse(os.environ.get('CM_USER_1'), os.environ.get('CM_USER_PASS_1'))
    # except Exception as e:
    #     logger.error(e)

    try:
        envanto.parse(os.environ.get('ELEM_USER'), os.environ.get('ELEM_USER_PASS'))
    except Exception as e:
        logger.error(e)

    try:
        yellowimgs.parse(os.environ.get('YIM_USER'), os.environ.get('YIM_USER_PASS'))
    except Exception as e:
        logger.error(e)

    # try:
    #     designcuts.parse(
    #         os.environ.get('DC_USER'),
    #         os.environ.get('BOT_MAIL_USER'),
    #         os.environ.get('BOT_MAIL_PASSWORD'),
    #         os.environ.get('BOT_MAIL_IMAP'),
    #         os.environ.get('DC_PARSE_FOLDER'),
    #     )
    # except Exception as e:
    #     logger.error(e)

    try:
        youworkforthem.parse(
            os.environ.get('YWFT_USER'),
            os.environ.get('YWFT_EMAIL'),
            os.environ.get('YWFT_PASS')
        )
    except Exception as e:
        logger.error(e)

    logger.info('Parsing sales done')


@sched.scheduled_job('cron', hour=0)
@logger.catch
def parse_items():
    logger.info('Start parsing items')
    try:
        creative.refresh_products(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))
    except Exception as e:
        logger.error(e)

    try:
        creative.refresh_products(os.environ.get('CM_USER_1'), os.environ.get('CM_USER_PASS_1'))
    except Exception as e:
        logger.error(e)

    try:
        envanto.refresh_products(os.environ.get('ELEM_USER'), os.environ.get('ELEM_USER_PASS'))
    except Exception as e:
        logger.error(e)

    try:
        yellowimgs.refresh_products(os.environ.get('YIM_USER'), os.environ.get('YIM_USER_PASS'))
    except Exception as e:
        logger.error(e)

    try:
        designcuts.refresh_products(os.environ.get('DC_USER'))
    except Exception as e:
        logger.error(e)

    try:
        youworkforthem.refresh_products(os.environ.get('YWFT_USER'), os.environ.get('YWFT_USER_ID'))
    except Exception as e:
        logger.error(e)

    logger.info('Parsing items done')


@sched.scheduled_job('cron', hour=7, minute=35)
@logger.catch
def test():
    logger.info('Start test parsing')
    youworkforthem.parse(
        os.environ.get('YWFT_USER'),
        os.environ.get('YWFT_EMAIL'),
        os.environ.get('YWFT_PASS')
    )


if __name__ == "__main__":
    logger.add(sink=send_tg_alarm, level='INFO')
    sched.start()
