from __future__ import print_function

import re
import sys
import json
import praw
import time
import warnings
import requests

import history

from jjkae_tools import replace_top_sticky, send_email, is_python_3
from reddit_password import get_spreaker_oauth2

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


class Twinnovation:
    def __init__(self, number, title, duration, monthstring, reddit_title=None, url=None, reddit_url=None,
                 desc=None):
        self.number = number
        self.title = title
        self.duration = duration
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "Twinnovation submission object: " + self.title

    def __str__(self):
        return self.__repr__()



def get_twins_info(depth=0):
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
            r = requests.get(
                'https://api.spreaker.com/v2/shows/1484314/episodes?oauth2_access_token={}'.format(get_spreaker_oauth2()),
                timeout=15.0,
            )
            j = json.loads(r.text)
            most_recent_ep = j['response']['items'][0]
            most_recent_ep_spreaker_id = j['response']['items'][0]['site_url'].split('/')[-1]
            r = requests.get(
                'https://api.spreaker.com/v2/episodes/{}?oauth2_access_token={}'.format(most_recent_ep_spreaker_id, get_spreaker_oauth2()),
                timeout=15.0,
            )
            episode_obj = json.loads(r.text)
            desc = episode_obj['response']['episode']['description']
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered spreaker Timeout. recursing.")
        time.sleep(3)
        return get_twins_info()
    except Exception as e:
        print("encountered spreaker error =(")
        print(e)
        time.sleep(3)
        return get_twins_info(depth=depth + 1)
    title = most_recent_ep['title']  # full title including number. `title` is like "86: Pants or Shorts Live at SXSW"
    url = most_recent_ep['site_url']
    duration_secs = most_recent_ep['duration'] // 1000
    if duration_secs < 3600:
        duration = '{}:{}'.format(duration_secs // 60, duration_secs % 60)
    else:
        duration = '{}:{}:{}'.format(duration_secs // 3600, (duration_secs % 3600) // 60, duration_secs % 60)
    [episode_num, title] = title.split(' ', maxsplit=1)  # now `title` is like "Pants or Shorts Live at SXSW"
    episode_num = int(episode_num)
    name = 'Twinnovation Episode {episode_num}: {title} [{duration}]'.format(**locals())
    reddit_title = name

    desc = desc.replace('"', "'").strip()
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    twins_obj = Twinnovation(
        number=episode_num,
        title=title,
        duration=duration,
        reddit_title=reddit_title,
        monthstring=history.this_monthstring(),
        url=url,
        desc=desc,
    )
    return twins_obj


def check_twins_and_post_if_new(mod_info, force_submit=False, testmode=False):
    twins_obj = get_twins_info()
    if not force_submit:
        if twins_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_twins(twins_obj, mod_info, testmode=testmode)
            break
        except requests.exceptions.HTTPError:
            print("HTTP error while trying to submit - retrying to resubmit")
            pass
        except praw.errors.AlreadySubmitted:
            print('Already submitted.')
            break
        except Exception as e:
            print("Error", e)
            break
    mod_info.foundlist.append(twins_obj.reddit_title)
    #mod_info.foundlist.append(twins_obj.duration)


def get_comment_text(twins_obj):
    comment = ''
    comment += '"' + twins_obj.desc + '"\n\n---\n\n###[Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_twins(twins_obj, mod_info, testmode=False, depth=0):
    """

    :type testmode: bool
    :type twins_obj: Twinnovation
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="twinnovation SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = 'jakeandamir'
    sub = mod_info.r.get_subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - twinnovation found: ", twins_obj.reddit_title)
        return

    try:
        submission = mod_info.r.submit('jakeandamir', twins_obj.reddit_title, url=twins_obj.url)
    except praw.errors.AlreadySubmitted as e:
        print(e)
        twins_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_twins(twins_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_twins(twins_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    sub.set_flair(submission, flair_text='NEW TWINNOVATION', flair_css_class='images')
    submission.approve()

    print("NEW twinnovation!!! WOOOOO!!!!")
    print(twins_obj.reddit_title)
    post_subreddit_comment(submission, twins_obj)
    twins_obj.reddit_url = submission.permalink
    replace_top_sticky(sub, submission)

    mod_info.past_history.add_twins(twins_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, twins_obj):
    while True:
        try:
            comment_text = get_comment_text(twins_obj)
            comment = submission.add_comment(comment_text)
            comment.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    twins_obj = (get_twins_info())
    import pdb; pdb.set_trace()
    print(twins_obj)
