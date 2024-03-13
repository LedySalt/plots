#!/usr/bin/env/ python3
from datetime import datetime, timedelta
import json
from pathlib import Path
import requests
from multiprocessing import Process

START = datetime(year=2022, month=7, day=8)
N_DAYS = 28 * 2
DIR = Path(__file__).resolve().parent / "loaded"
if not DIR.exists():
    DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://webrobo.mgul.ac.ru:3000/db_api_REST/calibr"


def write_sensors_data(day):
    print(day.strftime("Processing %d/%m/%Y"))
    fmt = day.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/day/{fmt}"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException:
        data = {}
    else:
        if response.ok:
            data = response.json()
        else:
            data = {}
    file = DIR / day.strftime("%Y-%m-%d.json")
    with file.open("w") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    print(f"File {file} saved")


for i in range(N_DAYS):
    date = START + timedelta(days=i)
    p = Process(target=write_sensors_data, args=(date, ))
    p.start()
