from __future__ import print_function

import sys
import time
import iiwy
#import lonely
import datetime
import jjkae_tools

from mod_stuff import mod_actions, ModInfo
from rewatch import episodes

force_submit_rewatch = False  # This causes mod_actions to post the rewatch the first iteration (i==1).
force_submit_iiwy = False
#force_submit_lnh = False

def get_timeout(default_timeout=5):
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%A')
    if (hour, day) in [
        (23, 'Sunday'), (0, 'Monday'), (1, 'Monday'), (2, 'Monday'),  # IIWY episodes
        (23, 'Wednesday'), (0, 'Thursday'), (1, 'Thursday'), (2, 'Thursday')  # IIWY bonus episodes
        #  (9, 'Friday'), (10, 'Friday') # Lonely & Horny
    ]:
        return 1
    else:
        return default_timeout


def mod_loop(mod_info, force_submit_rewatch=False):
    mod_actions(mod_info, force_submit_rewatch=force_submit_rewatch)

def iiwy_loop(mod_info, force_submit_iiwy=False):
    iiwy.check_iiwy_and_post_if_new(mod_info, force_submit=force_submit_iiwy)

#def lnh_loop(mod_info, force_submit_lnh=False):
#    lonely.check_lnh_and_post_if_new(mod_info, force_submit=force_submit_lnh)


def initialize_foundlist():
    iiwy_obj = iiwy.get_iiwy_info()
    print("Name of most recent IIWY is: \"" + iiwy_obj.title + "\"", "with URL", iiwy_obj.url,
          "and description", iiwy_obj.desc, "and sponsors", iiwy_obj.sponsor_list,
          "and duration", iiwy_obj.duration)
    foundlist = ["", iiwy_obj.number, iiwy_obj.duration]
    #  lnh_obj = lonely.get_lnh_info()
    #  print("Names of most recent LNH's are: \"", lnh_obj.titles, "\" with URLs ", lnh_obj.urls,
    #        "and duration ", lnh_obj.durations, sep='')
    #  lonely.append_to_foundlist(foundlist, lnh_obj)
    return foundlist

def main():
    global force_submit_iiwy, force_submit_rewatch, force_submit_lnh

    default_timeout = 5  # don't spam the servers :D

    jjkae_tools.start_test_thread(email_if_failures=True)

    foundlist = initialize_foundlist()

    next_episode = -1  # STARTS AT 1
    if len(sys.argv) > 1:
        next_episode = int(sys.argv[1])

    mod_info = ModInfo(next_episode, foundlist)

    if mod_info.next_episode > -1:
        print('Previous episode:', episodes[mod_info.next_episode - 2])
        print('Next episode to be posted:', episodes[mod_info.next_episode - 1])

    while True:
        iiwy_loop(mod_info, force_submit_iiwy)
        force_submit_iiwy = False  # Only do it once

        mod_loop(mod_info, force_submit_rewatch)
        force_submit_rewatch = False  # Only do it once

        #  lnh_loop(mod_info, force_submit_lnh)
        #  force_submit_lnh = False  # Only do it once

        timeout = get_timeout(default_timeout)

        if timeout != 0:
            time.sleep(timeout)

        jjkae_tools.printinfo(mod_info)
        mod_info.i += 1


if __name__ == "__main__":
    main()
