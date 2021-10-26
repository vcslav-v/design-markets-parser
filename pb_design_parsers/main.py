from apscheduler.schedulers.blocking import BlockingScheduler

from loguru import logger
import requests
import os
from pb_design_parsers import creative


sched = BlockingScheduler()


def send_tg_alarm(message):
    requests.post(
            'https://api.telegram.org/bot{token}/sendMessage?chat_id={tui}&text={text}'.format(
                token=os.environ.get('ALLERT_BOT_TOKEN'),
                tui=os.environ.get('ADMIN_TUI'),
                text=message,
            ))


@sched.scheduled_job('cron', hour=6, minute=40)
@logger.catch
def parse_creative_market():
    logger.info('Start parsing')
    creative.parse(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))


@sched.scheduled_job('cron', hour=6, minute=50)
@logger.catch
def parse_creative_market_csv():
    logger.info('Start data mining')
    creative.add_data(os.environ.get('CM_USER'))


if __name__ == "__main__":
    logger.add(sink=send_tg_alarm)
    sched.start()
