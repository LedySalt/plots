import math
import os
import warnings

from numpy import RankWarning
from pandas.errors import SettingWithCopyWarning
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import json
from tkinter import filedialog

from matplotlib.dates import num2date, date2num
from matplotlib.widgets import RangeSlider, RadioButtons, CheckButtons

warnings.simplefilter(action='ignore', category=DeprecationWarning)
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)
warnings.simplefilter(action='ignore', category=RankWarning)

matplotlib.use("TkAgg")

UNITS = {
    "Temperature": "$^o$C",
    "Pressure": "Torr",
    "Humidity": "%",
    "Perceived Temperature": "$^o$C",
    "Perceived": "Perception Units"
}

TIME_UNITS = {
    "As is": "0min",
    "1 Hour": "1h",
    "3 Hours": "3h",
    "1 Day": pd.Timedelta(1, "d")
}


def get_perceived(perceived_temp):
    if perceived_temp < -30:
        return 0
    if perceived_temp < -24:
        return 1
    if perceived_temp < -12:
        return 2
    if perceived_temp < 0:
        return 3
    if perceived_temp < 6:
        return 4
    if perceived_temp < 12:
        return 5
    if perceived_temp < 18:
        return 6
    if perceived_temp < 24:
        return 7
    if perceived_temp < 30:
        return 8
    return 9


def parse_json(filename):
    data = {
        "Date": [],
        "Temperature": [],
        "Pressure": [],
        "Humidity": [],
        "Name": []
    }
    raw_data = json.load(open(filename))
    for value in raw_data.values():
        if value["uName"] == "Тест Студии" or value["uName"] == 'Hydra-L' or value["uName"] == "Hydra-L1" or value[
            "uName"] == "Тест воздуха":
            temp = value["data"]["BME280_temp"]
            pressure = value["data"]["BME280_pressure"]
            humidity = value["data"]["BME280_humidity"]
        elif value["uName"] == "Паскаль" or value["uName"] == "Опорный барометр":
            temp = value["data"]["weather_temp"]
            pressure = value["data"]["weather_pressure"]
            humidity = 0
        elif value["uName"] == "Тест СБ":
            temp = value["data"]["weather_temp"]
            pressure = 0
            humidity = value["data"]["weather_humidity"]
        elif value["uName"] == "РОСА К-2":
            temp = value["data"]["weather_temp"]
            pressure = value["data"]["weather_pressure"]
            humidity = value["data"]["weather_humidity"]
        elif value["uName"] == "Pogodaiklimat":
            temp = value["data"]["Temperature"]
            pressure = value["data"]["Pressure"]
            humidity = value["data"]["Humidity"]
        elif value["uName"] == "Сервер СЕВ" or value["uName"] == "Сервер webrobo" or \
                value["uName"] == "Сервер dokuwiki" or value["uName"] == "Сервер dbrobo" or \
                value["uName"] == "Сервер K3edu":
            continue
        else:
            print(value["uName"])
            print(value)
            raise Exception("Name not found")
        data["Name"].append(f'{value["uName"]} ({value["serial"]})')
        data["Date"].append(value["Date"])
        data["Temperature"].append(float(temp))
        data["Pressure"].append(float(pressure))
        data["Humidity"].append(float(humidity))
    return pd.DataFrame(data)


def parse_csv(filename):
    name = ""
    with open(filename, encoding='ptcp154') as f:
        name = f.readline().split(';')[1]
    raw_data = pd.read_csv(filename, skiprows=1, sep=";", encoding='ptcp154').iloc[:, :-1]
    data = {"Date": raw_data["Date"]}
    data["Name"] = [name] * len(data["Date"])
    if "Тест Студии" in name or 'Hydra-L' in name or "Hydra-L1" in name or "Тест воздуха" in name:
        temp = raw_data["BME280_temp"]
        pressure = raw_data["BME280_pressure"]
        humidity = raw_data["BME280_humidity"]
    elif "Паскаль" in name or "Опорный барометр" in name:
        temp = raw_data["weather_temp"]
        pressure = raw_data["weather_pressure"]
        humidity = [0] * len(temp)
    elif "Тест СБ" in name:
        temp = raw_data["weather_temp"]
        pressure = [0] * len(temp)
        humidity = raw_data["weather_humidity"]
    elif "РОСА К-2" in name:
        temp = raw_data["weather_temp"]
        pressure = raw_data["weather_pressure"]
        humidity = raw_data["weather_humidity"]
    elif "Сервер СЕВ" in name or "Сервер webrobo" in name or \
            "Сервер dokuwiki" in name or "Сервер dbrobo" in name or \
            "Сервер K3edu" in name:
        raise Exception("This is data from server, not sensor!")
    else:
        print(name)
        print(raw_data)
        raise Exception("Name not found")
    data["Temperature"] = temp
    data["Pressure"] = pressure
    data["Humidity"] = humidity
    return pd.DataFrame(data)


def get_data_from_user():
    paths = filedialog.askopenfilenames(filetypes=[("Data files", ".csv .json")])
    data_list = []
    for path in paths:
        filename, extension = os.path.splitext(path)
        if extension == ".json":
            data_list.append(parse_json(path))
        elif extension == ".csv":
            data_list.append(parse_csv(path))
        else:
            raise Exception("Unrecognised file format")
    data = pd.concat(data_list, ignore_index=True)
    data["Date"] = pd.to_datetime(data["Date"])
    data.sort_values("Date", inplace=True)
    data["Perceived Temperature"] = data["Temperature"] - 0.4 * (data["Temperature"] - 10) * (
            1 - data["Humidity"] / 100)
    data["Perceived"] = data.apply(lambda x: get_perceived(x["Perceived Temperature"]), axis=1)
    return data


df = get_data_from_user()

fig = plt.figure("Practice", figsize=(23, 15))

ax = fig.add_axes([0.16, 0.1, 0.70, 0.85])

date_slider_ax = fig.add_axes([0.16, 0, 0.63, 0.05])
slider = RangeSlider(date_slider_ax, "Date", date2num(df["Date"].min()), date2num(df["Date"].max()),
                     valinit=(date2num(df["Date"].min()), date2num(df["Date"].max())), handle_style={"size": 30})

data_ax = fig.add_axes([0.005, 0.85, 0.11, 0.1])
data_radio_buttons = RadioButtons(data_ax,
                                  ['Temperature', "Pressure", "Humidity", "Perceived Temperature", "Perceived"])

window_ax = fig.add_axes([0.005, 0.74, 0.11, 0.1])
window_radio_buttons = RadioButtons(window_ax, ["As is", "1 Hour", "3 Hours", "1 Day"])

rolling_type_ax = fig.add_axes([0.005, 0.63, 0.11, 0.1])
rolling_type_buttons = RadioButtons(rolling_type_ax, ["Mean", "Min", "Max"])

plot_type_ax = fig.add_axes([0.005, 0.52, 0.11, 0.1])
plot_type_buttons = RadioButtons(plot_type_ax, ["Line plot", "Bar plot", "Scatter plot + Polyfit"])

names = df["Name"].unique()
names = sorted(names)
name_ax = fig.add_axes([0.885, 0.1, 0.11, 0.85])
name_buttons = CheckButtons(name_ax, names, actives=[True] + [False] * (len(names) - 1))


def select_data_range(selected_data_name, time_range, time_window, rolling_type):
    mask = (df["Date"] >= np.datetime64(num2date(time_range[0]))) & \
           (df["Date"] <= np.datetime64(num2date(time_range[1])))
    df_slice = df.loc[mask]
    if rolling_type == "Mean":
        df_slice["SelectedData"] = df_slice.rolling(time_window, on="Date")[selected_data_name].mean().dropna()
    elif rolling_type == "Min":
        df_slice["SelectedData"] = df_slice.rolling(time_window, on="Date")[selected_data_name].min().dropna()
    elif rolling_type == "Max":
        df_slice["SelectedData"] = df_slice.rolling(time_window, on="Date")[selected_data_name].max().dropna()
    return df_slice


def filter_by_device(data, device_name):
    return data[data["Name"] == device_name]


def plot_selected_graph(x, y, plot_type, label):
    if plot_type == "Line plot":
        ax.plot(x, y, label=label)
    elif plot_type == "Bar plot":
        ax.bar(x, y, label=label)
    elif plot_type == "Scatter plot + Polyfit":
        poly = np.poly1d(np.polyfit(date2num(x), y, 5))
        ax.plot(x, poly(date2num(x)))
        ax.scatter(x, y, label=label)


def draw_main_axis(data, plot_type, selected_data, device_names):
    ax.cla()
    for device_name in device_names:
        filtered_data = filter_by_device(data, device_name)
        plot_selected_graph(filtered_data["Date"], filtered_data["SelectedData"], plot_type, device_name)
    ax.ticklabel_format(axis="y", scilimits=(0, 3), useMathText=False)
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    ax.xaxis_date()
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    ax.set_xlabel("Date")
    ax.set_ylabel(f"{selected_data}, {UNITS[selected_data]}")
    ax.grid(True)
    ax.legend()
    plt.draw()


def get_names(selected):
    result = []
    for name, val in zip(names, selected):
        if val:
            result.append(name)
    return result


def update(s=0):
    selected_data_name = data_radio_buttons.value_selected
    time_range = slider.val
    time_window = TIME_UNITS[window_radio_buttons.value_selected]
    rolling_type = rolling_type_buttons.value_selected
    device_names = get_names(name_buttons.get_status())
    plot_type = plot_type_buttons.value_selected
    slider.valtext.set_text(f"{num2date(time_range[0]).date()} — {num2date(time_range[1]).date()}")
    selected_data = select_data_range(selected_data_name, time_range, time_window, rolling_type)
    draw_main_axis(selected_data, plot_type, selected_data_name, device_names)


update()
data_radio_buttons.on_clicked(update)
slider.on_changed(update)
window_radio_buttons.on_clicked(update)
rolling_type_buttons.on_clicked(update)
plot_type_buttons.on_clicked(update)
name_buttons.on_clicked(update)
plt.show()
