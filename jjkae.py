from __future__ import print_function

import sys
import time
import iiwy
import twins
import geoff
import datetime
import jjkae_tools

from mod_stuff import mod_actions, ModInfo
from rewatch import episodes

force_submit_rewatch = False  # This causes mod_actions to post the rewatch the first iteration (i==1).
force_submit_twins = False
force_submit_iiwy = False
force_submit_gtd = False


def get_timeout(default_timeout=5):
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%A')
    if (hour, day) in [
        (23, 'Sunday'), (0, 'Monday'), (1, 'Monday'), (2, 'Monday'),  # IIWY episodes
        (23, 'Wednesday'), (0, 'Thursday'), (1, 'Thursday'), (2, 'Thursday'),  # IIWY bonus episodes
        (23, 'Thursday'), (0, 'Friday'), (1, 'Friday'), (2, 'Friday'),  # twinnovation episodes
    ]:
        return 1
    else:
        return default_timeout


def mod_loop(mod_info, force_submit_rewatch=False):
    mod_actions(mod_info, force_submit_rewatch=force_submit_rewatch)


def iiwy_loop(mod_info, force_submit_iiwy=False):
    iiwy.check_iiwy_and_post_if_new(mod_info, force_submit=force_submit_iiwy)


def twins_loop(mod_info, force_submit_twins=False):
    twins.check_twins_and_post_if_new(mod_info, force_submit=force_submit_twins)


def gtd_loop(mod_info, force_submit_gtd=False):
    geoff.check_gtd_and_post_if_new(mod_info, force_submit=force_submit_gtd)


def initialize_foundlist():
    iiwy_obj = iiwy.get_iiwy_info()
    twins_obj = twins.get_twins_info()
    gtd_obj = geoff.get_gtd_info()
    print("Name of most recent IIWY is: \"" + iiwy_obj.title + "\"", "with URL", iiwy_obj.url,
          "and description", iiwy_obj.desc, "and sponsors", iiwy_obj.sponsor_list,
          "and duration", iiwy_obj.duration)
    print("Most recent Twinnovation is: {}".format(twins_obj.reddit_title))
    foundlist = ["", iiwy_obj.number, twins_obj.reddit_title, gtd_obj.reddit_title]
    return foundlist


def main():
    global force_submit_iiwy, force_submit_twins, force_submit_rewatch, force_submit_gtd

    default_timeout = 5  # don't spam the servers :D

    foundlist = initialize_foundlist()

    next_episode = -1  # STARTS AT 1
    if len(sys.argv) > 1:
        next_episode = int(sys.argv[1])

    mod_info = ModInfo(next_episode, foundlist)

    if mod_info.next_episode > -1:
        print('Previous episode:', episodes[mod_info.next_episode - 2])
        print('Next episode to be posted:', episodes[mod_info.next_episode - 1])

    jjkae_tools.start_test_thread(email_if_failures=True)

    past_exception_string = None
    while True:
        try:
            iiwy_loop(mod_info, force_submit_iiwy)
            force_submit_iiwy = False  # Only do it once

            twins_loop(mod_info, force_submit_twins)
            force_submit_twins = False  # Only do it once

            mod_loop(mod_info, force_submit_rewatch)
            force_submit_rewatch = False  # Only do it once

            if mod_info.i % 5 == 1:
                # do it 20% of the time. This is because Youtube pretty heavily rate limits requests, so we can't be
                # hitting the server 12 times a minute.
                gtd_loop(mod_info, force_submit_gtd)
                force_submit_gtd = False  # Only do it once

            timeout = get_timeout(default_timeout)

            if timeout != 0:
                time.sleep(timeout)

            jjkae_tools.printinfo(mod_info)
            mod_info.i += 1
        except (SystemExit, KeyboardInterrupt) as e:
            raise e
        except Exception as e:
            this_exception_string = "{} {}".format(type(e).__name__, str(e.args))
            print(this_exception_string)
            if past_exception_string != this_exception_string:
                jjkae_tools.send_email(subject="JAKE AND AMIR BOT ERROR", body=this_exception_string, to="popcorncolonel@gmail.com")
                print("SENT EMAIL!!!")
            print(this_exception_string)
            past_exception_string = this_exception_string
            time.sleep(1.0)
            pass


if __name__ == "__main__":
    main()
