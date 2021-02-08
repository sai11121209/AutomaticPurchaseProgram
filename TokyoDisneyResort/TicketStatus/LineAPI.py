import requests as rq
from GetTicketStatus import GTS
import os

try:
    from local_settings import *
except ImportError:
    import keep_alive

    keep_alive.keep_alive()


# 自分のBotのアクセストークンに置き換えてください
if os.getenv("TOKEN"):
    access_token = os.getenv("TOKEN")


def send_message(access_token, Datas):
    url = "https://notify-api.line.me/api/notify"
    access_token = access_token
    headers = {"Authorization": "Bearer " + access_token}
    message = "再販あり\n"
    for Key in Datas.keys():
        message += f"東京ディズニー{Key}\n"
        for Data in Datas[Key]:
            message += f"{Data}\n"
    payload = {"message": message}

    rq.post(url, headers=headers, params=payload)


import schedule
import time


def job():
    Datas = GTS()
    if Datas:
        send_message(access_token, Datas)
    else:
        pass


job()

# 1分ごとに実行
schedule.every(1).minutes.do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
