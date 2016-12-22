import json
import datetime


class History:
    def __init__(self, history_dict):
        self.history_dict = history_dict

    def __iter__(self):
        return iter(self.history_dict)

    def __getitem__(self, key):
        return self.history_dict[key]

    def write(self):
        with open("history.json", "w") as json_file:
            json.dump(self.history_dict, json_file, sort_keys=True, indent=4)

    def add_iiwy(self, iiwy):
        monthstring = iiwy.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'IIWY' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['IIWY'] = []
        self.history_dict[monthstring]['IIWY'].append({
            "title": iiwy.title,
            "reddit_url": iiwy.reddit_url,
            "number": iiwy.number,
            "duration": iiwy.duration
        })

    def add_gtd(self, gtd):
        monthstring = gtd.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'GTD' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['GTD'] = []
        self.history_dict[monthstring]['GTD'].append({
            "title": gtd.title,
            "reddit_url": gtd.reddit_url,
            "number": gtd.number,
        })

    def add_lnh(self, lnh):
        monthstring = lnh.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'LNH' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['LNH'] = []
        for title, duration in zip(lnh.titles, lnh.durations):
            self.history_dict[monthstring]['LNH'].append({
                "title": title,
                "duration": duration,
                "reddit_url": lnh.reddit_url
            })


def get_history():
    with open("history.json") as json_file:
        json_data = json.load(json_file)
    return History(json_data)


history = get_history()


def this_monthstring():
    today_datetime = datetime.datetime.now()
    month, year = today_datetime.strftime('%b'), today_datetime.strftime('%Y')
    return month + " " + year
