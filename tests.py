import unittest

from mod_stuff import ModInfo

class JjkaeTest(unittest.TestCase):
    foundlist = []
    mod_info = ModInfo(foundlist=foundlist)

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

    def test_nadd(self):
        import nadd
        nadd_obj = nadd.get_nadd_info()

        self.assertIsNotNone(nadd_obj.title)
        self.assertIsNotNone(nadd_obj.reddit_title)
        self.assertIsNotNone(nadd_obj.url)
        self.assertIsNotNone(nadd_obj.desc)
        self.assertIsNotNone(nadd_obj.monthstring)
        nadd.check_nadd_and_post_if_new(self.mod_info, testmode=True)

    def test_headgum(self):
        import headgum
        headgum_obj = headgum.get_headgum_info()

        self.assertIsNotNone(headgum_obj.title)
        self.assertIsNotNone(headgum_obj.reddit_title)
        self.assertIsNotNone(headgum_obj.url)
        self.assertIsNotNone(headgum_obj.desc)
        self.assertIsNotNone(headgum_obj.monthstring)
        self.assertIsNotNone(headgum_obj.episode_num)
        headgum.check_headgum_and_post_if_new(self.mod_info, testmode=True)

    def test_twins(self):
        import twins
        twins_obj = twins.get_twins_info()
        #self.assertIs(type(twins_obj.number), int)

        self.assertIsNotNone(twins_obj.title)
        self.assertIsNotNone(twins_obj.reddit_title)
        self.assertIsNotNone(twins_obj.url)
        self.assertIsNotNone(twins_obj.desc)
        self.assertIsNotNone(twins_obj.monthstring)
        twins.check_twins_and_post_if_new(self.mod_info, testmode=True)

    def test_iiwy(self):
        import iiwy
        iiwy_obj = iiwy.get_iiwy_info()
        #self.assertIs(type(iiwy_obj.number), int)

        self.assertIsNotNone(iiwy_obj.title)
        self.assertIsNotNone(iiwy_obj.reddit_title)
        self.assertIsNotNone(iiwy_obj.url)
        self.assertIsNotNone(iiwy_obj.desc)
        self.assertIsNotNone(iiwy_obj.monthstring)
        iiwy.check_iiwy_and_post_if_new(self.mod_info, testmode=True)

    def test_gtd(self):
        import geoff
        gtd_obj = geoff.get_gtd_info()
        self.assertIsNotNone(gtd_obj.title)
        self.assertIsNotNone(gtd_obj.reddit_title)
        self.assertIsNotNone(gtd_obj.url)
        self.assertIsNotNone(gtd_obj.desc)
        self.assertIsNotNone(gtd_obj.monthstring)
        self.assertIsNotNone(gtd_obj.ep_type)
        geoff.check_gtd_and_post_if_new(self.mod_info, testmode=True)

    def test_multiple_gtds(self):
        import geoff
        gtd_objs = geoff.get_gtd_info(topN=50)
        self.assertGreater(len(gtd_objs), 1)
        print('found a bunch of gtd objects: ')
        for obj in gtd_objs:
            print(obj)

    def test_jna(self):
        return
        import jakeandamir
        jna_obj = jakeandamir.get_jna_info()
        self.assertIsNotNone(jna_obj.title)
        self.assertIsNotNone(jna_obj.reddit_title)
        self.assertIsNotNone(jna_obj.url)
        self.assertIsNotNone(jna_obj.desc)
        self.assertIsNotNone(jna_obj.monthstring)
        self.assertIsNotNone(jna_obj.upload_date)
        jakeandamir.check_jna_and_post_if_new(self.mod_info, testmode=True)

    def test__prints(self):
        import jjkae_tools
        self.mod_info.foundlist = []
        for i in range(1, 153):
            self.mod_info.i = i
            jjkae_tools.printinfo(self.mod_info)
        self.mod_info.i = 1

    def test_mod_stuff(self):
        from mod_stuff import ModInfo, mod_actions

        mod_info = ModInfo(foundlist=[])
        mod_actions(mod_info, testmode=True, force_submit_rewatch=False)

        print("Tested mod actions")

    def test_rewatch_all_episodes_parsed(self):
        from rewatch import episodes
        for episode in episodes:
            self.assertIsNotNone(episode.date_str)
            self.assertIsNotNone(episode.title)
            self.assertIsNotNone(episode.url)
            self.assertIsNotNone(episode.duration)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(JjkaeTest)
    results = unittest.TextTestRunner(verbosity=0).run(suite)
    print('test failures: ', results.errors)


