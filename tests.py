import unittest

class JjkaeTest(unittest.TestCase):
    def test_load_history_json(self):
        import json
        with open("history.json") as json_file:
            json_data = json.load(json_file)
        import sys
        self.assertNotEqual(len(json_data), 0)

    def test_iiwy(self):
        import iiwy
        iiwy_obj = iiwy.get_iiwy_info()
        self.assertIs(type(iiwy_obj.number), int)
        self.assertIs(type(iiwy_obj.title), unicode)
        self.assertIs(type(iiwy_obj.reddit_title), unicode)
        self.assertIs(type(iiwy_obj.url), unicode)
        self.assertIs(type(iiwy_obj.desc), unicode)
        self.assertIs(type(iiwy_obj.sponsor_list), list)

# Returns the list of errors of the tests
def run_tests(verbosity=0):
    suite = unittest.TestLoader().loadTestsFromTestCase(JjkaeTest)
    results = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return results.errors

if __name__ == '__main__':
    run_tests()

