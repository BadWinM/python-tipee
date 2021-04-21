#!/usr/bin/env python3
# frank.villaro@infomaniak.com - DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE, etc.

import datetime
import os
import sys

import requests


def parse_time(str_time: str, default=None):
    if not str_time or str_time == "":
        return default
    return datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")


class Tipee:
    def __init__(self, instance: str):
        if instance[-1] != "/":
            instance += "/"
        self.instance = instance
        self.session = requests.Session()

    def login(self, username: str, password: str):
        url = self.instance + "api/sign-in"
        payload = {
            "username": username,
            "password": password,
        }
        r = self.session.post(url, json=payload)
        r.raise_for_status()

        self._get_me()

    def _get_me(self):
        url = self.instance + "brain/users/me"
        r = self.session.get(url)
        self.id = r.json()["id"]

    def get_timechecks(self, day=None):
        if not day:
            day = datetime.datetime.now()

        str_day = day.strftime("%Y-%m-%d")

        url = self.instance + f"api/employees/{self.id}/workday?date={str_day}"
        r = self.session.get(url)
        r.raise_for_status()

        js = r.json()
        return js.get("timechecks", [])

    def get_worktime(self, day=None):
        total_working_time = datetime.timedelta()

        for timecheck in self.get_timechecks(day):
            time_in = parse_time(timecheck["time_in"])
            time_out = parse_time(timecheck["time_out"], datetime.datetime.now())

            delta = time_out - time_in
            total_working_time += delta

        return total_working_time

    def punch(self):
        url = self.instance + "brain/timeclock/timechecks"
        payload = {
            "person": self.id,
            "timeclock": "Linux",
        }
        r = self.session.post(url, json=payload)
        r.raise_for_status()


if __name__ == "__main__":
    t = Tipee(os.environ["TIPEE_URL"])
    t.login(os.environ["TIPEE_USERNAME"], os.environ["TIPEE_PASSWORD"])
    today = datetime.datetime.now()

    if len(sys.argv) > 1 and sys.argv[1] == "punch":
        t.punch()
        print("The clock has been punched ! 🤜⏰")

    print(f'TODAY {today.strftime("%Y-%m-%d")}\n----------------\ntimes: ', end="")
    for timecheck in t.get_timechecks(today):
        for field in ["time_in", "time_out"]:
            dt = parse_time(timecheck[field], None)
            if dt is not None:
                print(f'{dt.strftime("%H:%M")} ', end="")
    print(f"\ntotal worktime: {t.get_worktime(today)}")


# vim: set ts=4 sw=4 et:
