import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import inquirer


class TokyoDisneyResort:
    def __init__(self):
        self.set_data()
        if self.get_park() == "東京ディズニーランド":
            self.select_park_day_1 = "01"
        else:
            self.select_park_day_1 = "02"
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 200)
        self.PurchaseState = False
        self.set_url()
        self.job()

    def check_none(self, num):
        if num:
            return num
        else:
            return 0

    def set_park(self, park):
        self.park = park

    def set_date_y(self, date_y):
        self.date_y = date_y

    def set_date_m(self, date_m):
        self.date_m = date_m

    def set_date_d(self, date_d):
        self.date_d = date_d

    def set_child(self, child):
        self.child = child

    def set_junior(self, junior):
        self.junior = junior

    def set_adult(self, adult):
        self.adult = adult

    def set_url(self):
        self.url = f"https://reserve.tokyodisneyresort.jp/sp/ticket/search/?parkTicketGroupCd=01&route=2&selectParkDay1={self.select_park_day_1}&useDays=1&numOfJunior={self.get_junior()}&useDateFrom={self.get_date_y()}{str(self.get_date_m()).zfill(2)}{str(self.get_date_d()).zfill(2)}&parkTicketSalesForm=1&numOfAdult={self.get_adult()}&numOfChild={self.get_child()}"

    def get_park(self):
        return self.park

    def get_date_y(self):
        return self.date_y

    def get_date_m(self):
        return self.date_m

    def get_date_d(self):
        return self.date_d

    def get_child(self):
        return self.child

    def get_junior(self):
        return self.junior

    def get_adult(self):
        return self.adult

    def get_url(self):
        return self.url

    def set_data(self):
        parks = [
            inquirer.List(
                "size",
                message="来園予定パーク選択",
                choices=["東京ディズニーランド", "東京ディズニーシー"],
                carousel=True,
            )
        ]
        print("東京ディズニーリゾート自動チケット購入プログラム v1.0")
        print("本プログラムは回線状態によっては非常に不安定な動作をする可能性があります。", end="")
        input()
        print("また本プログラムはチケット確保後のログイン処理等はセキュリティーの関係上実装しておりません。", end="")
        input()
        print(
            "そのためチケット購入のための決済処理は手入力で進めてください。(チケット確保後一定時間経過によりタイムアウトしてしまうため素早く決済完了をお願いします。)",
            end="",
        )
        input()
        self.set_park(inquirer.prompt(parks)["size"])
        self.set_date_y(int(self.check_none(input("来園予定日(西暦): "))))
        self.set_date_m(int(self.check_none(input("来園予定日(月): "))))
        self.set_date_d(int(self.check_none(input("来園予定日(日): "))))
        print("一度の購入で合計五枚までです。")
        self.set_child(int(self.check_none(input("来園人数(小人（4才～小学生）4,900円): "))))
        self.set_junior(int(self.check_none(input("来園人数(中人（中学生・高校生）6,900円): "))))
        self.set_adult(int(self.check_none(input("来園人数(大人（18才以上）8,200円): "))))
        os.system("cls")
        print("以下入力内容の確認です。")
        if self.get_child() + self.get_junior() + self.get_adult() <= 5:
            print(f"来園予定パーク: {self.get_park()}")
            print(
                f"{self.get_date_y()}/{str(self.get_date_m()).zfill(2)}/{str(self.get_date_d()).zfill(2)}"
            )
            if self.get_child() != 0:
                print(f"来園人数(小人（4才～小学生）4,900円): {self.get_child()}")
            if self.get_junior() != 0:
                print(f"来園人数(中人（中学生・高校生）6,900円): {self.get_junior()}")
            if self.get_adult() != 0:
                print(f"来園人数(大人（18才以上）8,200円): {self.get_adult()}")
            print("--------------------------------------")
            print(
                f"合計金額(税込み): {self.get_child()*4900+self.get_junior()*6900+self.get_adult()*8200}"
            )
            start_state = [
                inquirer.List(
                    "size", message="開始前確認", choices=["終了", "修正", "開始"], carousel=True,
                )
            ]
            state = inquirer.prompt(start_state)["size"]
            if state == "終了":
                exit(0)
            elif state == "修正":
                self.set_data
            else:
                print("10秒後Chromeが起動し自動購入処理を開始されます。")
                print("途中で処理を終了したい場合は'Ctrl + C'で終了可能です。")
                time.sleep(10)
        else:
            print("一度の購入で5枚以上選択されました。最初に戻ります。")
            time.sleep(3)
            os.system("cls")
            self.set_data()

    def button_click(self, button_text):
        buttons = self.driver.find_elements_by_tag_name("button")

        for button in buttons:
            if button.text == button_text:
                button.click()
                break

    def job(self):
        self.driver.get(self.get_url())
        try:
            while 1:
                try:
                    self.wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                "#list-ticket-group > div > section > div.elm-fadeup > section.list-purchae-view.section-module.elm-progressive-reveal.is-visible > ul > li > button",
                            )
                        )
                    )
                    self.button_click("購入手続きに進む")
                    self.driver.execute_script(
                        "document.getElementsByClassName('js-mm-next button disabled')[0].className='js-mm-next button';"
                    )
                    self.button_click("確認した")
                    if len(self.driver.find_elements_by_class_name("messages")) == 1:
                        self.wait.until(
                            EC.element_to_be_clickable(
                                (
                                    By.CSS_SELECTOR,
                                    "#firstPage > div.ui-popup-container.pop.in.ui-popup-active > div > a",
                                )
                            )
                        )
                        time.sleep(2)
                        self.driver.find_element_by_css_selector(
                            "#firstPage > div.ui-popup-container.pop.in.ui-popup-active > div > a"
                        ).click()
                    else:
                        self.PurchaseState = True
                        break
                except selenium.common.exceptions.StaleElementReferenceException:
                    self.driver.get(self.get_url())
                    continue
            if self.PurchaseState:
                while 1:
                    time.sleep(100)
            else:
                self.driver.quit()
        except KeyboardInterrupt:
            self.driver.quit()


if __name__ == "__main__":
    pass
