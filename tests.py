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
        iiwy_obj.title = iiwy_obj.title.encode('utf-8')
        iiwy_obj.desc = iiwy_obj.desc.encode('utf-8')
        iiwy_obj.url = iiwy_obj.url.encode('utf-8')
        self.assertEqual(iiwy_obj.title, str(iiwy_obj.title))
        self.assertEqual(iiwy_obj.reddit_title, str(iiwy_obj.reddit_title))
        self.assertEqual(iiwy_obj.url, str(iiwy_obj.url))
        self.assertEqual(iiwy_obj.desc, str(iiwy_obj.desc))
        self.assertEqual(iiwy_obj.monthstring, str(iiwy_obj.monthstring))
        self.assertIs(type(iiwy_obj.sponsor_list), list)
        iiwy.check_iiwy_and_post_if_new(self.mod_info, testmode=True)

    def test_lnh(self):
        import lonely
        lnh_obj = lonely.get_lnh_info()
        self.assertEqual(len(lnh_obj.titles), 2)

        lnh_obj.titles = (lnh_obj.titles[0].encode('utf-8'),
                          lnh_obj.titles[1].encode('utf-8'))
        lnh_obj.urls = (lnh_obj.urls[0].encode('utf-8'),
                        lnh_obj.urls[1].encode('utf-8'))
        lnh_obj.durations = (lnh_obj.durations[0].encode('utf-8'),
                        lnh_obj.durations[1].encode('utf-8'))

        self.assertEqual(str(lnh_obj.titles[0]), lnh_obj.titles[0])
        self.assertEqual(str(lnh_obj.titles[1]), lnh_obj.titles[1])

        self.assertEqual(len(lnh_obj.durations), 2)
        self.assertEqual(str(lnh_obj.durations[0]), lnh_obj.durations[0])
        self.assertEqual(str(lnh_obj.durations[1]), lnh_obj.durations[1])

        self.assertEqual(len(lnh_obj.urls), 2)
        self.assertEqual(str(lnh_obj.urls[0]), lnh_obj.urls[0])
        self.assertEqual(str(lnh_obj.urls[1]), lnh_obj.urls[1])

        self.assertEqual(str(lnh_obj.reddit_title), lnh_obj.reddit_title)
        self.assertEqual(str(lnh_obj.desc), lnh_obj.desc)
        self.assertEqual(str(lnh_obj.monthstring), lnh_obj.monthstring)

        lonely.check_lnh_and_post_if_new(self.mod_info, testmode=True)

        import history
        hist_obj = history.get_history()
        hist_obj.add_lnh(lnh_obj)

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
