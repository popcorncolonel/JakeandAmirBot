import unittest

class JjkaeTest(unittest.TestCase):
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
        self.assertIs(type(iiwy_obj.sponsor_list), list)

    def test_prints(self):
        import jjkae_tools
        from rewatch import episodes
        from mod_stuff import ModInfo
        foundlist = []
        next_episode = 100
        mod_info = ModInfo(next_episode=next_episode, r=None, user=None, paw=None, i=1, foundlist=foundlist, episodes=episodes, past_history=None)
        for i in range(1, 153):
            mod_info.i = i
            jjkae_tools.printinfo(mod_info)

    def test_mod_stuff(self):
        from mod_stuff import ModInfo, mod_actions
        from rewatch import episodes
        import praw, reddit_password, history
        r = praw.Reddit(user_agent = 'JakeandAmir program by /u/popcorncolonel')
        r.config.decode_html_entities = True # This makes titles that contain HTML stuff (like '&amp;') be the actual character (like '&') in unicode.
        user = 'JakeandAmirBot'
        paw = reddit_password.get_password()

        mod_info = ModInfo(15, r, user, paw, 1, [], episodes, history.get_history())
        mod_actions(mod_info, testmode=False)
        print("Tested mod actions")

# Returns the list of errors of the tests
def run_tests(verbosity=0):
    suite = unittest.TestLoader().loadTestsFromTestCase(JjkaeTest)
    results = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return results.errors

if __name__ == '__main__':
    run_tests()

