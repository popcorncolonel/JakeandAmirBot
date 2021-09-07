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

from jjkae_tools import replace_top_sticky, send_email, is_python_3

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


class IIWY:
    def __init__(self, number, title, monthstring, reddit_title=None, url=None, reddit_url=None,
                 desc=None):
        self.number = number
        self.title = title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "IIWY submission object: " + self.title

    def __str__(self):
        return self.__repr__()



def to_reddit_url(link):
    '''
    Turns "google.com" into "[google](google.com)"
    '''
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_iiwy_info(depth=0):
    title = None
    name = None
    url = None
    desc = None
    episode_num = None
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rss_loc = 'https://www.omnycontent.com/d/playlist/77bedd50-a734-42aa-9c08-ad86013ca0f9/1c4b3626-f520-4ce1-b3a4-ad8e00138f76/45e167c5-a3df-46b4-bd69-ad8e00138f7f/podcast.rss'
            rss = feedparser.parse(rss_loc)
            episode = rss.entries[0]
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered spreaker Timeout. recursing.")
        time.sleep(3)
        return get_iiwy_info()
    except Exception as e:
        print("encountered spreaker error =(")
        print(e)
        time.sleep(3)
        return get_iiwy_info(depth=depth + 1)
    name = episode.title  # name is the full title. `title` is like "501: First Date"
    if 'Episode' not in name:
        name = 'Episode ' + name
    if ':' in name:  # "Episode 191: The Emotionary" -> "The Emotionary"
        title = name.split(':')[1].strip()
    else:
        title = name
    url = episode.links[-1].href
    reddit_title = name

    desc = episode.content[-1].value
    if desc is None:
        desc = ''
    desc = re.sub('<.*?>', '', desc).replace('  ', ' ').replace('  ', ' ')
    # Episode 69: Lmao -> 69
    search = re.search('\d+', name.split(':')[0].split()[-1].strip())
    if search is not None:
        episode_num = search.group()
        episode_num = int(episode_num)
    try:
        if 'If I Were You' not in name:
            name = "If I Were You " + name
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print("encountered iiwy error :((((")
        print(e)
        time.sleep(1)

    desc = desc.replace('"', "'").strip()
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    iiwy_obj = IIWY(number=episode_num, title=title, 
                    reddit_title=reddit_title, monthstring=history.this_monthstring(), url=url,
                    desc=desc)
    return iiwy_obj


def check_iiwy_and_post_if_new(mod_info, force_submit=False, testmode=False):
    iiwy_obj = get_iiwy_info()
    if not force_submit:
        if iiwy_obj.number in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_iiwy(iiwy_obj, mod_info, testmode=testmode)
            break
        except requests.exceptions.HTTPError:
            print("HTTP error while trying to submit - retrying to resubmit")
            pass
        except Exception as e:
            print("Error", e)
            break
    mod_info.foundlist.append(iiwy_obj.number)


def get_comment_text(iiwy_obj):
    comment = ''
    comment += '"' + iiwy_obj.desc + '"\n\n---\n\n###Links\n\n [If I Were You Bingo](http://iiwybingo.appspot.com)\n\n [Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_iiwy(iiwy_obj, mod_info, testmode=False, depth=0):
    """

    :type testmode: bool
    :type iiwy_obj: IIWY
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="IIWY SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = 'jakeandamir'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - IIWY found: ", iiwy_obj.reddit_title)
        return

    try:
        submission = sub.submit(iiwy_obj.reddit_title, url=iiwy_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        iiwy_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_iiwy(iiwy_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_iiwy(iiwy_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW IIWY!!! WOOOOO!!!!")
    print(iiwy_obj.reddit_title)
    post_subreddit_comment(submission, iiwy_obj)
    iiwy_obj.reddit_url = submission.permalink
    replace_top_sticky(sub, submission)

    mod_info.past_history.add_iiwy(iiwy_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, iiwy_obj):
    while True:
        try:
            comment_text = get_comment_text(iiwy_obj)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    iiwy_obj = (get_iiwy_info())
    import pdb; pdb.set_trace()
    print(iiwy_obj)
