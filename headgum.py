from __future__ import print_function

import re
import sys
import json
import praw
import prawcore
import time
import warnings
import requests
import feedparser

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


class Headgum:
    def __init__(self, title, monthstring,
                 reddit_title=None, url=None, reddit_url=None, desc=None, episode_num=None, duration=None):
        self.title = title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc
        self.episode_num = episode_num
        self.duration = duration

    def __repr__(self):
        return "Headgum submission object: " + self.title

    def __str__(self):
        return self.__repr__()


def get_headgum_info(depth=0):
    title = None
    name = None
    url = None
    desc = None
    filename = None
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rss_loc = 'https://feeds.simplecast.com/hvQ33fkq'
            rss = feedparser.parse(rss_loc)
            episode = rss.entries[0]
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered request Timeout. recursing.")
        time.sleep(3)
        return get_headgum_info()
    except Exception as e:
        print("encountered request error =(")
        print(e)
        time.sleep(3)
        return get_headgum_info(depth=depth + 1)
    title = episode['title_detail']['value']  # Full title, with num. `title` is like "9: Subjective Trivia (w/ Zach Dunn!)"
    if ':' in title:
        num = title.split(':')[0]
    episode_num = None
    try:
        episode_num = int(num)
        title = ':'.join(title.split(':')[1:]).strip()
    except ValueError:
        print('yikes')
        print(title)
    url = episode['links'][0].href
    name = 'The Headgum Podcast Episode {episode_num}: {title}'.format(**locals())
    reddit_title = name
    desc = episode.summary_detail['value']
    desc = re.sub('<.*?>', '\n', desc).replace('  ', ' ').replace('  ', ' ')  # replace <br> with \n, prevent weird space formatting i guess?

    desc = desc.replace('"', "'").strip()
    desc = desc.split('\n\n')[0]
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    duration=episode.itunes_duration if 'itunes_duration' in episode.keys() else None
    headgum_obj = Headgum(
        title=title,
        reddit_title=reddit_title,
        monthstring=history.this_monthstring(),
        url=url,
        desc=desc,
        episode_num=episode_num,
        duration=duration,
    )
    return headgum_obj


def check_headgum_and_post_if_new(mod_info, force_submit=False, testmode=False):
    headgum_obj = get_headgum_info()
    if not force_submit:
        if headgum_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_headgum(headgum_obj, mod_info, testmode=testmode)
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
    mod_info.foundlist.append(headgum_obj.reddit_title)


def get_comment_text(headgum_obj):
    comment = ''
    comment += '"' + headgum_obj.desc + '"\n\n---\n\n###[Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_headgum(headgum_obj, mod_info, testmode=False, depth=0):
    """
    :type testmode: bool
    :type headgum_obj: Headgum
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="HEADGUM SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = 'jakeandamir'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - Headgum found: ", headgum_obj.reddit_title)
        return

    try:
        submission = sub.submit(headgum_obj.reddit_title, url=headgum_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        headgum_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_headgum_obj(headgum_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_headgum(headgum_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW Headgum Pod!!! WOOOOO!!!!")
    print(headgum_obj.reddit_title)
    post_subreddit_comment(submission, headgum_obj)
    headgum_obj.reddit_url = submission.permalink
    #set_bottom_sticky(sub, submission)
    replace_top_sticky(sub, submission)

    mod_info.past_history.add_headgum_obj(headgum_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, headgum_obj):
    while True:
        try:
            comment_text = get_comment_text(headgum_obj)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    headgum_obj = get_headgum_info()
    import pdb; pdb.set_trace()
    print(headgum_obj)

