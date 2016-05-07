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
