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

    def add_abbc_obj(self, abbc_obj):
        monthstring = abbc_obj.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'abbc' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['abbc'] = []
        if hasattr(abbc_obj, 'duration'):
            self.history_dict[monthstring]['abbc'].append({
                "title": abbc_obj.title,
                "reddit_url": abbc_obj.reddit_url,
                "duration": abbc_obj.duration,
            })
        else:
            self.history_dict[monthstring]['abbc'].append({
                "title": abbc_obj.title,
                "reddit_url": abbc_obj.reddit_url,
            })

    def add_nadd_obj(self, nadd_obj):
        monthstring = nadd_obj.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'nadd' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['nadd'] = []
        if hasattr(nadd_obj, 'duration'):
            self.history_dict[monthstring]['nadd'].append({
                "title": nadd_obj.title,
                "reddit_url": nadd_obj.reddit_url,
                "number": nadd_obj.number,
                "duration": nadd_obj.duration,
            })
        else:
            self.history_dict[monthstring]['nadd'].append({
                "title": nadd_obj.title,
                "reddit_url": nadd_obj.reddit_url,
                "number": nadd_obj.number,
            })

    def add_revue_obj(self, revue_obj):
        monthstring = revue_obj.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'revue' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['revue'] = []
        self.history_dict[monthstring]['revue'].append({
            "title": revue_obj.title,
            "reddit_url": revue_obj.reddit_url,
        })

    def add_twins_obj(self, twins_obj):
        monthstring = twins_obj.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'twinnovation' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['twinnovation'] = []
        if hasattr(twins_obj, 'duration'):
            self.history_dict[monthstring]['twinnovation'].append({
                "title": twins_obj.title,
                "reddit_url": twins_obj.reddit_url,
                "number": twins_obj.number,
                "duration": twins_obj.duration,
            })
        else:
            self.history_dict[monthstring]['twinnovation'].append({
                "title": twins_obj.title,
                "reddit_url": twins_obj.reddit_url,
                "number": twins_obj.number,
            })

    def add_iiwy(self, iiwy):
        monthstring = iiwy.monthstring
        if monthstring not in self.history_dict:
            self.history_dict[monthstring] = dict()
        if 'IIWY' not in self.history_dict[monthstring]:
            self.history_dict[monthstring]['IIWY'] = []
        if hasattr(iiwy, 'duration'):
            self.history_dict[monthstring]['IIWY'].append({
                "title": iiwy.title,
                "reddit_url": iiwy.reddit_url,
                "number": iiwy.number,
                "duration": iiwy.duration,
            })
        else:
            self.history_dict[monthstring]['IIWY'].append({
                "title": iiwy.title,
                "reddit_url": iiwy.reddit_url,
                "number": iiwy.number,
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
            #"number": gtd.number,
            "ep_type": gtd.ep_type,
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
