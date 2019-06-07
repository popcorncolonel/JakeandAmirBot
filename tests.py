import unittest

from mod_stuff import ModInfo

class JjkaeTest(unittest.TestCase):
    foundlist = []
    next_episode = 100
    mod_info = ModInfo(next_episode=next_episode, foundlist=foundlist)

    def __init__(self, *args, **kwargs):
        super(JjkaeTest, self).__init__(*args, **kwargs)
        self.mod_info = JjkaeTest.mod_info

    def test_login(self):
        print("Logging in...")
        self.mod_info.login()
        print("Logged in.")

    def test_load_history_json(self):
        import json
        with open("history.json") as json_file:
            json_data = json.load(json_file)
        self.assertNotEqual(len(json_data), 0)

    def test_abbc(self):
        import abbc
        abbc_obj = abbc.get_abbc_info()

        self.assertIsNotNone(abbc_obj.title)
        self.assertIsNotNone(abbc_obj.reddit_title)
        self.assertIsNotNone(abbc_obj.url)
        #self.assertIsNotNone(abbc_obj.duration)
        self.assertIsNotNone(abbc_obj.desc)
        self.assertIsNotNone(abbc_obj.monthstring)
        abbc.check_abbc_and_post_if_new(self.mod_info, testmode=True)

    def test_nadd(self):
        import nadd
        nadd_obj = nadd.get_nadd_info()

        self.assertIsNotNone(nadd_obj.title)
        self.assertIsNotNone(nadd_obj.reddit_title)
        self.assertIsNotNone(nadd_obj.url)
        #self.assertIsNotNone(nadd_obj.duration)
        self.assertIsNotNone(nadd_obj.desc)
        self.assertIsNotNone(nadd_obj.monthstring)
        nadd.check_nadd_and_post_if_new(self.mod_info, testmode=True)

    def test_twins(self):
        import twins
        twins_obj = twins.get_twins_info()
        #self.assertIs(type(twins_obj.number), int)

        self.assertIsNotNone(twins_obj.title)
        self.assertIsNotNone(twins_obj.reddit_title)
        self.assertIsNotNone(twins_obj.url)
        #self.assertIsNotNone(twins_obj.duration)
        self.assertIsNotNone(twins_obj.desc)
        self.assertIsNotNone(twins_obj.monthstring)
        twins.check_twins_and_post_if_new(self.mod_info, testmode=True)

    def test_iiwy(self):
        import iiwy
        iiwy_obj = iiwy.get_iiwy_info()
        self.assertIs(type(iiwy_obj.number), int)

        self.assertIsNotNone(iiwy_obj.title)
        self.assertIsNotNone(iiwy_obj.reddit_title)
        self.assertIsNotNone(iiwy_obj.url)
        self.assertIsNotNone(iiwy_obj.desc)
        self.assertIsNotNone(iiwy_obj.monthstring)
        self.assertIs(type(iiwy_obj.sponsor_list), list)
        iiwy.check_iiwy_and_post_if_new(self.mod_info, testmode=True)

    def test_gtd(self):
        import geoff
        gtd_obj = geoff.get_gtd_info()
        self.assertIsNotNone(gtd_obj.title)
        self.assertIsNotNone(gtd_obj.reddit_title)
        self.assertIsNotNone(gtd_obj.url)
        self.assertIsNotNone(gtd_obj.desc)
        self.assertIsNotNone(gtd_obj.monthstring)
        geoff.check_gtd_and_post_if_new(self.mod_info, testmode=True)

    def test__prints(self):
        import jjkae_tools
        self.mod_info.foundlist = []
        for i in range(1, 153):
            self.mod_info.i = i
            jjkae_tools.printinfo(self.mod_info)
        self.mod_info.i = 1

    def test_mod_stuff(self):
        from mod_stuff import ModInfo, mod_actions, post_monthly_discussion

        mod_info = ModInfo(next_episode=15, foundlist=[])
        mod_actions(mod_info, testmode=True)
        post_monthly_discussion(mod_info, testmode=True)

        print("Tested mod actions")
