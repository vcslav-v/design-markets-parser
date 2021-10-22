from apscheduler.schedulers.blocking import BlockingScheduler

from loguru import logger
import requests
import os


sched = BlockingScheduler()


def send_tg_alarm(message):
    requests.post(
            'https://api.telegram.org/bot{token}/sendMessage?chat_id={tui}&text={text}'.format(
                token=os.environ.get('ALLERT_BOT_TOKEN'),
                tui=os.environ.get('ADMIN_TUI'),
                text=message,
            ))


@logger.catch
@sched.scheduled_job('cron', hour=1)
def parse_creative_market():
    pass


if __name__ == "__main__":
    # logger.add(sink=send_tg_alarm)
    # sched.start()
    parse_creative_market()
