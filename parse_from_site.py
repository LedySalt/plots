from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_html_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        body = None
    else:
        if r.ok:
            r.encoding = r.apparent_encoding
            body = r.text
    return body


def parse_for_month(date):
    print(date.strftime("Parsing %d/%m/%Y"))
    data = {
        "Date": [],
        "uName": [],
        "serial": [],
        "data": [],
    }
    html = get_html_page(
        f"http://pogodaiklimat.ru/weather.php?id=27612&bday={date.day}&fday={date.day}&amonth={date.month}&ayear={date.year}&bot=2")
    soup = BeautifulSoup(html, features="html.parser")
    table = soup.find('div', class_="archive-table")
    table_date = table.findAll('table')[0].findAll('tr')
    table_value = table.findAll('table')[1].findAll('tr')
    for raw_date, raw_data in list(zip(table_date, table_value))[1:]:
        date_values = [value.text for value in raw_date.findAll('td')]
        raw_data_values = [value.text for value in raw_data.findAll('td')]
        device_data = {}
        data["Date"].append((date + timedelta(hours=int(date_values[0]))).strftime("%Y-%m-%d %H:%M:%S"))
        device_data["Temperature"] = str(float(raw_data_values[5]))
        device_data["Pressure"] = str(float(raw_data_values[11]) / 1.333)  # Conversion from hPa to torr
        device_data["Humidity"] = str(float(raw_data_values[7]))
        data["data"].append(device_data)
        data["uName"].append("Pogodaiklimat")
        data["serial"].append("00")
    return pd.DataFrame(data)


days_to_parse = 28
date_start = datetime(year=2022, month=7, day=8)
data_list = []
for i in range(days_to_parse):
    data_list.append(parse_for_month(date_start + timedelta(days=i)))
data = pd.concat(data_list, ignore_index=True)
data.to_json("pogodaiklimat.json", orient="index")
