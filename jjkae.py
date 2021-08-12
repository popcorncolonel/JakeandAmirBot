from __future__ import print_function

import sys
import time
import iiwy
import twins
import abbc
import nadd
import revue
import headgum
import geoff
import jakeandamir
import datetime
import jjkae_tools

from mod_stuff import mod_actions, ModInfo
from rewatch import episodes

force_submit_rewatch = False  # This causes mod_actions to post the rewatch the first iteration (i==1).
force_submit_abbc = False
force_submit_nadd = False
force_submit_revue = False
force_submit_headgum = False
force_submit_twins = False
force_submit_iiwy = False
force_submit_gtd = False
force_submit_jna = False


def get_timeout(default_timeout):
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%A')
    if (hour, day) in [
        (23, 'Sunday'), (0, 'Monday'), # IIWY episodes
        (23, 'Monday'), (0, 'Tuesday'), (1, 'Tuesday'), (2, 'Tuesday'), (3, 'Tuesday'), # ReviewRevue, I guess
        (23, 'Wednesday'), (0, 'Thursday'), (1, 'Thursday'), (2, 'Thursday'), (3, 'Thursday'), # NaddPod
        (10, 'Thursday'), (11, 'Thursday'), (12, 'Thursday'), (13, 'Thursday'), (14, 'Thursday'), (15, 'Thursday'), # HG vids
        (23, 'Thursday'), (0, 'Friday'), (1, 'Friday'), (2, 'Friday'),  # twinnovation,headgum episodes
        (15, 'Friday'), (16, 'Friday'), (17, 'Friday'),  # 8bit book club episodes
    ]:
        return 5
    else:
        return default_timeout


def mod_loop(mod_info, force_submit_rewatch=False):
    mod_actions(mod_info, force_submit_rewatch=force_submit_rewatch)


def iiwy_loop(mod_info, force_submit_iiwy=False):
    iiwy.check_iiwy_and_post_if_new(mod_info, force_submit=force_submit_iiwy)


def twins_loop(mod_info, force_submit_twins=False):
    twins.check_twins_and_post_if_new(mod_info, force_submit=force_submit_twins)


def nadd_loop(mod_info, force_submit_nadd=False):
    nadd.check_nadd_and_post_if_new(mod_info, force_submit=force_submit_nadd)


def revue_loop(mod_info, force_submit_revue=False):
    revue.check_revue_and_post_if_new(mod_info, force_submit=force_submit_revue)


def headgum_loop(mod_info, force_submit_headgum=False):
    headgum.check_headgum_and_post_if_new(mod_info, force_submit=force_submit_headgum)


def abbc_loop(mod_info, force_submit_abbc=False):
    abbc.check_abbc_and_post_if_new(mod_info, force_submit=force_submit_abbc)


def gtd_loop(mod_info, force_submit_gtd=False):
    geoff.check_gtd_and_post_if_new(mod_info, force_submit=force_submit_gtd)


def jna_loop(mod_info, force_submit_jna=False):
    jakeandamir.check_jna_and_post_if_new(mod_info, force_submit=force_submit_jna)


def initialize_foundlist():
    iiwy_obj = iiwy.get_iiwy_info()
    twins_obj = twins.get_twins_info()
    nadd_obj = nadd.get_nadd_info()
    revue_obj = revue.get_revue_info()
    headgum_obj = headgum.get_headgum_info()
    abbc_obj = abbc.get_abbc_info()
    gtd_obj = geoff.get_gtd_info()
    jna_obj = jakeandamir.get_jna_info()
    print("Name of most recent IIWY is: \"" + iiwy_obj.title + "\"", "with URL", iiwy_obj.url,
          "and description", iiwy_obj.desc, "and sponsors", iiwy_obj.sponsor_list,
          "and duration", iiwy_obj.duration)
    print("Most recent Twinnovation is: {}".format(twins_obj.reddit_title))
    print("Most recent NaddPod is: {}".format(nadd_obj.reddit_title))
    print("Most recent Review Revue is: {}".format(revue_obj.reddit_title))
    print("Most recent Headgum Pod is: {}".format(headgum_obj.reddit_title))
    print("Most recent 8 bit book club is: {}".format(abbc_obj.reddit_title))
    print("Most recent Jake and Amir is: {}".format(jna_obj.reddit_title))
    foundlist = ["", iiwy_obj.number, twins_obj.reddit_title, nadd_obj.reddit_title, revue_obj.reddit_title, headgum_obj.reddit_title, abbc_obj.reddit_title, gtd_obj.reddit_title, jna_obj.reddit_title]
    return foundlist


def main():
    global force_submit_iiwy, force_submit_twins, force_submit_nadd, force_submit_revue, force_submit_headgum, force_submit_abbc, force_submit_rewatch, force_submit_gtd, force_submit_jna

    default_timeout = 20  # don't spam the servers :D

    foundlist = initialize_foundlist()

    mod_info = ModInfo(foundlist)

    time.sleep(5)
    jjkae_tools.start_test_thread(email_if_failures=True)

    past_exception_string = None
    while True:
        try:
            iiwy_loop(mod_info, force_submit_iiwy)
            force_submit_iiwy = False  # Only do it once

            twins_loop(mod_info, force_submit_twins)
            force_submit_twins = False  # Only do it once

            nadd_loop(mod_info, force_submit_nadd)
            force_submit_nadd = False  # Only do it once

            revue_loop(mod_info, force_submit_revue)
            force_submit_revue = False  # Only do it once

            headgum_loop(mod_info, force_submit_headgum)
            force_submit_headgum = False  # Only do it once

            #abbc_loop(mod_info, force_submit_abbc)
            #force_submit_abbc = False  # Only do it once

            mod_loop(mod_info, force_submit_rewatch)
            force_submit_rewatch = False  # Only do it once

            # Do it 10% of the time. This is because Youtube pretty heavily rate limits requests, so we can't be
            # hitting the server 12 times a minute.
            if mod_info.i % 10 == 1:
                gtd_loop(mod_info, force_submit_gtd)
                force_submit_gtd = False  # Only do it once

                jna_loop(mod_info, force_submit_jna)
                force_submit_jna = False  # Only do it once

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
