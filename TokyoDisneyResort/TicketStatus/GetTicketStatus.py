import json
import sys
import time
import queue
import pytz
import threading
import traceback
import requests
import datetime
import jpholiday
import calendar
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from urllib import parse


def GTS(ParksPara):
    def query_worker(query_queue):
        try:
            query = query_queue.get()
            responses.append(
                {
                    "response": requests.post(
                        url, data=parse.urlencode(query).encode(), headers=headers
                    ),
                    "useDateFrom": query["useDateFrom"],
                    "commodityCd": query["commodityCd"],
                }
            )
            query_queue.task_done()
        except:
            responses.append({"response": "error"})

    maintenance_start_str = "03:00"
    maintenance_end_str = "05:00"
    maintenance_start = dt.strptime(maintenance_start_str, "%H:%M")
    maintenance_end = dt.strptime(maintenance_end_str, "%H:%M")

    headers = {
        "Host": "reserve.tokyodisneyresort.jp",
        "Connection": "keep-alive",
        "Content-Length": "52",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://reserve.tokyodisneyresort.jp",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://reserve.tokyodisneyresort.jp/sp/ticket/search/?parkTicketGroupCd=01&route=2&selectParkDay1=01&useDays=1&numOfJunior=0&useDateFrom=20210212&parkTicketSalesForm=1&numOfAdult=2&numOfChild=0&errorCd=3012",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8,de;q=0.7",
        "Cookie": "_ga=GA1.2.664613894.1596458172; __pp_uid=ls7sfgOLuBr6a2ib1JWQ1AxSnvxFahrx; __td_signed=true; _tdim=4a07193c-380b-4c3c-fb29-0fa7283432f4; __zlcmid=zVjKeYWR1pdgcz; _a1_f=71ae03f7-408a-45a7-806c-a218d33b16c1; _a1_u=7b312bcb-da99-4a1b-85dc-78475a8bb510; _ts_yjad=1599451699270; snexid=56d53208-6f67-4f55-84a3-fe62fdaa5e0e; SWID=ae69d61f-b510-4f9f-b90b-31d514be8f34; _gcl_au=1.1.1089915872.1605713036; _abck=CC1D761EF761A937B299B3308C006A21~0~YAAQ1wpPaMTKCr91AQAAjMytBQQdA8cgG97fmYN5lFov0ZpJYmEF7RgKTw5jOgTYegyceQhnXHk3fNxBH1IzSnIpj75YPCD7gPxVpuy4p1yslz7wBAyZ37//APp+g9oZ1468UFVf3xfy+jpkIt2FJshC58yKLoFVLN2FpteFl6OGHk3O3BXGrC/WtIU80OO5zq6C4KZ5PunbNIjT8RDJRjBm7ToEzWTKJPaRBEU64vOWFTtUXTEtbv4EhacqT/JBBhzwPUrhJ2yBSBxTJYwTY3D386BNrw8jD8qfuEXGkOxSycLjjpxl/SGw2slbW4LPqGdl0T5IJR6BGIVYIx8cG5E=~-1~-1~-1; _td=cdfd7d23-3e45-4617-a404-9a47ca79f98a; _im_id.1002516=c61f588beca04e87.1596458173.13.1606413098.1606413049.; JSESSIONID=BE203D9CAC34DD4A73A1DE6B1F5390F1-n1; bm_sz=B9FD62B03FDC479BDA0B3F7FE0ADF6DD~YAAQ1wpPaFYTwz13AQAAYcIAgAryo3BTOKq2zY0vuBGyzcAr1D+M36NZ35mYO1XFaZyBa3skt9WX04gcYCBg+2k5t7n26NONMUtylUl/ScO4vt07rTS5/4slFdCMHgkZh3Y1AwFJr3gdQ/FJ9WHrBydNmupV2H2s5xJXqYBbX5j5ARyA/zWeGygP5znnCGlaZa5uBGMuiQ32rA==; bm_mi=CA7974BE48EED9E98056B6D854DF979A~TSGD3C2rE9oIfjmqpPUASWZLvNFyy9LO7xCavJJ/uindlX4gZCZrTtlCl0vvZ2anSm9bv8HPUbpyASsn7513PPKU8sW3iLkvekvl2ue5am2j3bJaQXg1423oQaQpTHs0W3dvh9a9JpLMX8pA4YO0g/bVUWnNXRKc8bxu2Ntg2ZsCEzJHlqhYUEB92gXd54j0pL+vXsVMBdpK493jcGOsxLGpVOmgVzDcRl5UpZ6M3yThYXoqT0O7lcASMs0OznAND6j/ZUxRzjcA595l/RCMxA==; bm_sv=CB27C7ABF7C6C04E222D68E46A8C9447~mRoQ6zl1GUWNkcBONDndMEn6aapKdSuZB0sVdWYKImKRlVw/CbaUQ87feVp0DWQAbWJ9p8/os02TuJ/dOeyHoJ64HQb6qF5XLatwkRWqzztGy5siQdVSyUxvL0MhmKCbScTRqeBqU4fLVSTqryZgDvd6DFcQgBxr2fWt0q5t1Zg=; ak_bmsc=5ADD514C19A048EE01415EE974F6A0C9684F0AD7BF0E0000CDC420604F6F5C61~plg/StNZjTxWi0I4DpdFzkvuJ37STs3b9AXSZd/rQksnuRGzsUO+RyEGy5pRcUK4ArdFtTshNgkLdrM1UogTlIHYojkR6agFPyw5tw/tf9cCJ0tr9yW5h6eGTVlWK8YYh2n5aYf59yub5ZhjC+OpWUc5cN90c3ASwN8uDFDgBbeitn9ZBGHQw1OCjEV4f0V362IM4OQqf+qPByB+BKSQncoM/pRh57SXhG+0U0dwdaE2CYolmHITiT4KIOpAM7zNa1yPkUmHCEbbQ/1DwSIygggt/6fqcJ3M+dbEA+yaInpMw=; AWSALB=6p+SrnHWTgORB0rTSM3LSGQUg3iKuVFUT+6Pz3nuF9W3gH+6kY1KR4BQmQfb1lP4L4sVJRXE2FhjGbtd4RYw4SfQ9avxMmTF2kOMY8yYdwNUFklV8PsylYsmw0Tr; AWSALBCORS=6p+SrnHWTgORB0rTSM3LSGQUg3iKuVFUT+6Pz3nuF9W3gH+6kY1KR4BQmQfb1lP4L4sVJRXE2FhjGbtd4RYw4SfQ9avxMmTF2kOMY8yYdwNUFklV8PsylYsmw0Tr; akavpau_vp_reserve=1612766306~id=40d7df234127bf563dc18e8687ca8a85",
    }
    Available = {
        "ランド": [],
        "シー": [],
    }
    url = "https://reserve.tokyodisneyresort.jp/ticket/ajax/checkSaleable/"
    table_datas = []
    responses = []
    ResponseTimeStart = time.time()
    start = dt.now(pytz.timezone("Asia/Tokyo")) + datetime.timedelta(days=1)
    end = (
        dt.now(pytz.timezone("Asia/Tokyo"))
        + relativedelta(months=1)
        + datetime.timedelta(days=1)
    )
    table_datas = []
    # 新種別チケット移行日
    ChangeTicketTypeDate = dt(2021, 3, 20, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo"))

    SpecialTicketTypeDate_start = dt(
        2021, 3, 29, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
    )
    SpecialTicketTypeDate_end = dt(
        2021, 4, 2, 23, 59, tzinfo=pytz.timezone("Asia/Tokyo")
    )

    for Value in ParksPara.values():
        for n in range((end - start).days):
            check = start + timedelta(n)
            day_index = check.weekday()  # => 1
            if check < ChangeTicketTypeDate:
                commodityCd = Value[0]
            else:
                commodityCd = Value[3]
            """
            elif (
                jpholiday.is_holiday_name(check)
                or calendar.day_name[day_index] == "Saturday"
                or calendar.day_name[day_index] == "Sunday"
                or SpecialTicketTypeDate_start <= check <= SpecialTicketTypeDate_end
            ):
                commodityCd = Value[1]
                print("A")
            """
            table_datas.append(
                {
                    "_xhr": "",
                    "useDateFrom": f"{check.year}{str(check.month).zfill(2)}{str(check.day).zfill(2)}",
                    "commodityCd": commodityCd,
                }
            )

    # queueを設定
    query_queue = queue.Queue()
    for table_data in table_datas:
        query_queue.put(table_data)

    # Thread start
    while not query_queue.empty():
        w_thread = threading.Thread(target=query_worker, args=(query_queue,))
        w_thread.start()

    # wait all thread are ended.
    query_queue.join()

    for res in responses:
        try:
            res["response"].raise_for_status()
            if res.get("error"):
                ResponseTimeEnd = time.time()
                ResponseTime = ResponseTimeEnd - ResponseTimeStart
                print("ReadTimeout")
                return (3, ResponseTime, res["error"])
            elif res["response"].json()["saleStatusEticket"] == "1":
                check = {
                    "year": res["useDateFrom"][:4],
                    "month": res["useDateFrom"][4:6],
                    "day": res["useDateFrom"][6:],
                }
                Available[
                    [
                        Key
                        for Key, Values in ParksPara.items()
                        for Value in Values
                        if Value == res["commodityCd"]
                    ][0]
                ].append(
                    check["year"]
                    + "/"
                    + check["month"].zfill(2)
                    + "/"
                    + check["day"].zfill(2)
                )
                print(
                    check["year"]
                    + "/"
                    + check["month"].zfill(2)
                    + "/"
                    + check["day"].zfill(2)
                )
        # 403等の処理
        except requests.exceptions.RequestException as e:
            print(e)
            ResponseTimeEnd = time.time()
            ResponseTime = ResponseTimeEnd - ResponseTimeStart
            now = dt.now(pytz.timezone("Asia/Tokyo"))
            if maintenance_start.time() <= now.time() <= maintenance_end.time():
                return (4, ResponseTime, "ServerError")
            elif e.response.status_code == 403:
                return (2, ResponseTime, e)
            else:
                print(e)
        except json.decoder.JSONDecodeError as e:
            ResponseTimeEnd = time.time()
            ResponseTime = ResponseTimeEnd - ResponseTimeStart
            exc = traceback.format_exception_only(type(e), e)[0].rstrip("\n")
            if "line 8 column 1 (char 7)" in exc:
                print(exc)
            else:
                now = dt.now(pytz.timezone("Asia/Tokyo"))
                if maintenance_start.time() <= now.time() <= maintenance_end.time():
                    return (4, ResponseTime, "ServerError")
                else:
                    return (3, ResponseTime, exc)
        except KeyError:
            print("Server Maintenance")
            ResponseTimeEnd = time.time()
            ResponseTime = ResponseTimeEnd - ResponseTimeStart
            return (4, ResponseTime, "ServerError")
    if len(Available["ランド"]) != 0 or len(Available["シー"]) != 0:
        ResponseTimeEnd = time.time()
        ResponseTime = ResponseTimeEnd - ResponseTimeStart
        for Key in Available.keys():
            Available[Key] = sorted(Available[Key])
        print("Available")
        print(Available)
        return (1, ResponseTime, Available)
    else:
        ResponseTimeEnd = time.time()
        ResponseTime = ResponseTimeEnd - ResponseTimeStart
        print("NoAvailable")
        return (0, ResponseTime, "NoAvailable")


if __name__ == "__main__":
    pass
