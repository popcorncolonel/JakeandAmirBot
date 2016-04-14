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
        self.assertIn(type(iiwy_obj.title), {unicode, str})
        self.assertIn(type(iiwy_obj.reddit_title), {unicode, str})
        self.assertIn(type(iiwy_obj.url), {unicode, str})
        self.assertIn(type(iiwy_obj.desc), {unicode, str})
        self.assertIn(type(iiwy_obj.monthstring), {unicode, str})
        self.assertIs(type(iiwy_obj.sponsor_list), list)
        iiwy.check_iiwy_and_post_if_new(self.mod_info, testmode=True)

    def test_lnh(self):
        import lonely
        lnh_obj = lonely.get_lnh_info()
        self.assertEqual(len(lnh_obj.titles), 2)
        self.assertIn(type(lnh_obj.titles[0]), {unicode, str})
        self.assertIn(type(lnh_obj.titles[1]), {unicode, str})

        self.assertEqual(len(lnh_obj.durations), 2)
        self.assertIn(type(lnh_obj.durations[0]), {unicode, str})
        self.assertIn(type(lnh_obj.durations[1]), {unicode, str})

        self.assertEqual(len(lnh_obj.urls), 2)
        self.assertIn(type(lnh_obj.urls[0]), {unicode, str})
        self.assertIn(type(lnh_obj.urls[1]), {unicode, str})

        self.assertIn(type(lnh_obj.reddit_title), {unicode, str})
        self.assertIn(type(lnh_obj.desc), {unicode, str})
        self.assertIn(type(lnh_obj.monthstring), {unicode, str})

        lonely.check_lnh_and_post_if_new(self.mod_info, testmode=True)

    def test__prints(self):
        import jjkae_tools
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
