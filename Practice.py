import requests
from bs4 import BeautifulSoup
import math
import time
from time import sleep
import datetime
import schedule
from datetime import timedelta
from selenium.webdriver.common.keys import Keys
from selenium import webdriver

options = webdriver.ChromeOptions()
# 必須
options.add_argument("--headless")
options.add_argument("--disable-gpu")
# headlessでは不要そうな機能
options.add_argument("--disable-desktop-notifications")
options.add_argument("--disable-extensions")
# UA
# options.add_argument('--user-agent=puepue')
# 言語
options.add_argument("--lang=ja")
# 画像を読み込まないで軽くする
options.add_argument("--blink-settings=imagesEnabled=false")

options.add_argument("--proxy-server='direct://'")
options.add_argument("--proxy-bypass-list=*")
driver = webdriver.Chrome(chrome_options=options)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 10)  # 指定したdriverに対して最大で10秒間待つように設定する

driver.set_window_size(1045, 722)  # window size change

url1 = "https://t"
url2 = input("取りたいチケットのURL>")
login = "gmail.com"
password = "k"

start = input("開始時間>")
start1 = datetime.datetime.strptime(start, "%H:%M:%S").time()
start2 = datetime.datetime.combine(datetime.date.today(), start1) - datetime.timedelta(
    minutes=2
)
start3 = start2.strftime("%H:%M:%S")


r = requests.get("https://ntp-a1.nict.go.jp/cgi-bin/jst")
soup = BeautifulSoup(r.text, "lxml")

t1 = soup.find("body").string
t2 = t1.rstrip("\n")
t3 = time.time()
t4 = float(t2) - t3

if t4 >= 0:
    t5 = 0
    t6 = math.ceil(t4)
    t7 = t4 - t6

else:
    t5 = -t4
    t6 = 0
    t7 = 0

start5 = datetime.datetime.combine(datetime.date.today(), start1) + datetime.timedelta(
    seconds=t6
)
start6 = start5.strftime("%H:%M:%S")


def Login():
    driver.get(url1)
    print(datetime.datetime.now())
    print("ログイン出来ました。")


def Main():
    sleep(t5)
    sleep(t7)
    driver.get(url2)

    driver.find_element_by_name("c").submit()
    print(datetime.datetime.now())
    print("get")
    sleep(5)
    driver.quit()


schedule.every().day.at(start3).do(Login)
schedule.every().day.at(start6).do(Main)
while True:
    schedule.run_pending()
    time.sleep(0.1)
