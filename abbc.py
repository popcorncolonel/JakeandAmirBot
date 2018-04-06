# 'abbc' as in 'eight bit book club', it's pronounced 'ayte' get it?
from __future__ import print_function

import re
import sys
import json
import praw
import prawcore
import time
import warnings
import requests

import history

from jjkae_tools import replace_top_sticky, set_bottom_sticky, send_email, is_python_3

html_parser = None
if is_python_3():
    import html
    html_parser = html
else:
    import HTMLParser
    html_parser = HTMLParser.HTMLParser()


python_3 = False
if sys.version_info >= (3, 0):
    python_3 = True
    from bs4 import BeautifulSoup
else:
    from BeautifulSoup import BeautifulSoup

DEFAULT_STR = ''


class ABBC:
    def __init__(self, title, duration, monthstring,
                 reddit_title=None, url=None, reddit_url=None, desc=None):
        self.title = title
        self.duration = duration
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "abbc submission object: " + self.title

    def __str__(self):
        return self.__repr__()


def get_abbc_info(depth=0):
    title = None
    name = None
    url = None
    desc = None
    episode_num = None
    filename = None
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            abbc_id = '6fd9b6ab-2307-444a-9e15-088ff1ae0c2e'
            r = requests.get(
                'https://art19.com/episodes?series_id={}&sort=created_at'.format(abbc_id),
                headers={'Accept': 'application/vnd.api+json', 'Authorization': 'token="test-token", credential="test-credential"'},
                timeout=15.0,
            )
            j = json.loads(r.text)
            most_recent_ep = j['data'][-1]['attributes']
            most_recent_ep_id = j['data'][-1]['id']
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered request Timeout. recursing.")
        time.sleep(3)
        return get_abbc_info()
    except Exception as e:
        print("encountered request error =(")
        print(e)
        time.sleep(3)
        return get_abbc_info(depth=depth + 1)
    title = most_recent_ep['title']  # full title. `title` is like "Mega Man 2: The Novel"
    url = 'https://art19.com/shows/8-bit-book-club/episodes/{}'.format(most_recent_ep_id)
    """
    duration_secs = most_recent_ep['duration'] // 1000
    if duration_secs < 3600:
        duration = '{:02d}:{:02d}'.format(duration_secs // 60, duration_secs % 60)
    else:
        duration = '{}:{:02d}:{:02d}'.format(duration_secs // 3600, (duration_secs % 3600) // 60, duration_secs % 60)
    """
    duration = None
    name = '8 Bit Book Club: {title}'.format(**locals())
    reddit_title = name
    desc = most_recent_ep['description']
    desc = re.sub('<.*?>', '\n', desc).replace('  ', ' ').replace('  ', ' ')  # replace <br> with \n, prevent weird space formatting i guess?

    desc = desc.replace('"', "'").strip()
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    abbc_obj = ABBC(
        title=title,
        duration=duration,
        reddit_title=reddit_title,
        monthstring=history.this_monthstring(),
        url=url,
        desc=desc,
    )
    return abbc_obj


def check_abbc_and_post_if_new(mod_info, force_submit=False, testmode=False):
    abbc_obj = get_abbc_info()
    if not force_submit:
        if abbc_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_abbc(abbc_obj, mod_info, testmode=testmode)
            break
        except requests.exceptions.HTTPError:
            print("HTTP error while trying to submit - retrying to resubmit")
            pass
        except prawcore.exceptions.ServerError:
            print('Already submitted.')
            break
        except Exception as e:
            print("Error", e)
            break
    mod_info.foundlist.append(abbc_obj.reddit_title)


def get_comment_text(abbc_obj):
    comment = ''
    comment += '"' + abbc_obj.desc + '"\n\n---\n\n###[Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_abbc(abbc_obj, mod_info, testmode=False, depth=0):
    """
    :type testmode: bool
    :type abbc_obj: abbc
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="abbc SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = '8bitbookclub'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - abbc found: ", abbc_obj.reddit_title)
        return

    try:
        submission = sub.submit(abbc_obj.reddit_title, url=abbc_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        abbc_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_abbc_obj(abbc_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_abbc(abbc_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW abbc!!! WOOOOO!!!!")
    print(abbc_obj.reddit_title)
    post_subreddit_comment(submission, abbc_obj)
    abbc_obj.reddit_url = submission.permalink
    set_bottom_sticky(sub, submission)

    mod_info.past_history.add_abbc_obj(abbc_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, abbc_obj):
    while True:
        try:
            comment_text = get_comment_text(abbc_obj)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    abbc_obj = (get_abbc_info())
    import pdb; pdb.set_trace()
    print(abbc_obj)

