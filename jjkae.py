from __future__ import print_function

import sys
import time
import iiwy
import tests
import history
import datetime
import warnings

from rewatch import episodes
from mod_stuff import mod_actions, ModInfo

# have to create a reddit_password.py file with a get_password() function
import reddit_password

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import praw

force_submit_rewatch = False # This causes mod_actions to post the rewatch the first iteration (i==1).
force_submit_iiwy = False

def get_timeout(default_timeout=5):
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%A')
    if (hour, day) in [
            (23, 'Sunday'), (0, 'Monday'), (1, 'Monday'), (2, 'Monday'), # IIWY episodes
            (23, 'Wednesday'), (0, 'Thursday'), (1, 'Thursday'), (2, 'Thursday') # IIWY bonus episodes
        ]:
        return 1
    else:
        return default_timeout


def mod_loop(mod_info, force_submit_rewatch=False):
    if mod_info.next_episode > -1:
        mod_actions(mod_info, force_submit_rewatch)


def iiwy_loop(mod_info, force_submit_iiwy=False):
    iiwy.check_iiwy_and_post_if_new(mod_info, force_submit=force_submit_iiwy)


def test_before_running():
    errors = tests.run_tests()
    if errors != []:
        for error in errors:
            print(error)
        sys.exit()

def initialize_foundlist():
    iiwy_obj = iiwy.get_iiwy_info()
    print("Name of most recent IIWY is: \"" + iiwy_obj.title + "\"", "with URL", iiwy_obj.url,
          "and description", iiwy_obj.desc, "and sponsors", iiwy_obj.sponsor_list,
          "and duration", iiwy_obj.duration)
    foundlist = [""]
    foundlist.append(iiwy_obj.number)
    foundlist.append(iiwy_obj.duration)
    return foundlist


def main():
    global force_submit_iiwy, force_submit_rewatch

    i = 1
    default_timeout = 5 #don't spam the servers :D
    r = praw.Reddit(user_agent = 'JakeandAmir program by /u/popcorncolonel')
    r.config.decode_html_entities = True # This makes titles that contain HTML stuff (like '&amp;') be the actual character (like '&') in unicode.
    user = 'JakeandAmirBot'
    paw = reddit_password.get_password()

    test_before_running()

    past_history = history.get_history()
    foundlist = initialize_foundlist()

    next_episode = -1
    if len(sys.argv) > 1:
        next_episode = int(sys.argv[1])

    mod_info = ModInfo(next_episode, r, user, paw, i, foundlist, episodes, past_history) # STARTS AT 1

    if mod_info.next_episode > -1:
        print('Previous episode:', episodes[mod_info.next_episode-2])
        print('Next episode to be posted:', episodes[mod_info.next_episode-1])

    while True:
        iiwy_loop(mod_info, force_submit_iiwy)
        force_submit_iiwy = False # Only do it once

        mod_loop(mod_info, force_submit_rewatch)
        force_submit_rewatch = False # Only do it once

        timeout = get_timeout(default_timeout)

        if timeout != 0:
            time.sleep(timeout)

        mod_info.i += 1

if __name__ == "__main__":
    main()