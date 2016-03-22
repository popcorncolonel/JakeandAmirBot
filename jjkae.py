from __future__ import print_function

import calendar
import datetime
import requests
import sys
import time
import warnings
import webbrowser

import history
import iiwy
import tests
from mod_stuff import mod_actions
from rewatch import episodes

python_3 = False
if sys.version_info >= (3, 0):
    python_3 = True
else:
    pass

# have to create a reddit_password.py file with a get_password() function
import reddit_password

open_in_browser = False

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import praw

DEFAULT_STR = ''
debug = False

r = praw.Reddit(user_agent = 'JakeandAmir program by /u/popcorncolonel')
user = 'JakeandAmirBot'
paw = reddit_password.get_password()
subreddit = 'jakeandamir'

sub = r.get_subreddit(subreddit)
r.config.decode_html_entities = True

next_episode = -1 # START AT 1
if len(sys.argv) > 1:
    next_episode = int(sys.argv[1])

if next_episode > -1:
    print('Previous episode:', episodes[next_episode-2])
    print('Next episode to be posted:', episodes[next_episode-1])
    time.sleep(3)

timeout = default_timeout = 5 #don't spam the servers :D

past_history = history.get_history()

def adjust_timeout(default_timeout):
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%A')
    if (hour, day) in [
            (23, 'Sunday'), (0, 'Monday'), (1, 'Monday'), (2, 'Monday'), # IIWY episodes
            (23, 'Wednesday'), (0, 'Thursday'), (1, 'Thursday'), (2, 'Thursday') # IIWY bonus episodes
        ]:
        return 1
    else:
        return default_timeout

############################ LOGIC #############################

day = datetime.datetime.now().strftime('%A')

iiwy_obj = iiwy.get_iiwy_info()
print("Name of most recent IIWY is: \"" + iiwy_obj.title + "\"", "with URL", iiwy_obj.url,
      "and description", iiwy_obj.desc, "and sponsors", iiwy_obj.sponsor_list,
      "and duration", iiwy_obj.duration)


i = 1

errors = tests.run_tests()
if errors != []:
    for error in errors:
        print(error)
    sys.exit()

foundlist = [DEFAULT_STR]
foundlist.append(iiwy_obj.number)
foundlist.append(iiwy_obj.duration)

while True:
    iiwy.check_iiwy(i, foundlist, debug, r, user, paw, episodes, past_history, open_in_browser, next_episode)
    i += 1

    if next_episode > -1:
        mod_actions(next_episode, debug, r, user, paw, day)
        day = today_datetime.strftime('%A')

    adjust_timeout(default_timeout)

    if timeout != 0:
        time.sleep(timeout)

