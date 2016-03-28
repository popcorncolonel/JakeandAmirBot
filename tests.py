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
        foundlist = []
        next_episode = 100
        for i in range(1, 150):
            jjkae_tools.printinfo(i, episodes, foundlist, next_episode)

# Returns the list of errors of the tests
def run_tests(verbosity=0):
    suite = unittest.TestLoader().loadTestsFromTestCase(JjkaeTest)
    results = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return results.errors

if __name__ == '__main__':
    run_tests()

