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


class NADD:
    def __init__(self, title, monthstring,
                 number=None, reddit_title=None, url=None, reddit_url=None, desc=None):
        self.title = title
        self.monthstring = monthstring
        self.number = number
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "NaddPod submission object: " + self.title

    def __str__(self):
        return self.__repr__()


def get_nadd_info(depth=0):
    title = None
    name = None
    url = None
    desc = None
    episode_num = None
    filename = None
    if depth > 3:
        send_email(subject="NADD GETINFO ERROR", body="IDK depth={}".format(depth), to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rss_loc = 'https://www.omnycontent.com/d/playlist/77bedd50-a734-42aa-9c08-ad86013ca0f9/4dbfc420-53a4-40c6-bbc7-ad8d012bc602/6ede3615-a245-4eae-9087-ad8d012bc631/podcast.rss'
            rss = feedparser.parse(rss_loc)
            episode = rss.entries[0]
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered request Timeout. recursing.")
        time.sleep(3)
        return get_nadd_info()
    except Exception as e:
        print("encountered request error =(")
        print(e)
        time.sleep(3)
        return get_nadd_info(depth=depth + 1)
    orig_title = episode.title  # full title including number. `title` is like "Eldermourne - Ep. 32: People on the Inside"
    url = episode.links[-1].href
    episode_num = None
    title = orig_title
    if ': ' in orig_title:
        [episode_num, title] = orig_title.split(': ', maxsplit=1)  # now `title` is like "Dark Ritual (The Moonstone Saga)"
        episode_num_string = episode_num.split(' ')[-1]  # Ep. 5 -> 5, 'BONUS EPISODE' -> 'EPISODE'
        if episode_num_string.isdigit():
            episode_num = int(episode_num_string)
    if episode_num is not None:
        name = 'Episode {episode_num}: {title}'.format(**locals())
    else:
        name = 'Not Another D&D Podcast: {orig_title}'.format(**locals())
    reddit_title = name
    desc = episode.content[-1].value
    desc = re.sub('<.*?>', '\n', desc).replace('  ', ' ').replace('  ', ' ')  # replace <br> with \n, prevent weird space formatting i guess?

    desc = desc.replace('"', "'").strip()
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    nadd_obj = NADD(
        number=episode_num,
        title=title,
        reddit_title=reddit_title,
        monthstring=history.this_monthstring(),
        url=url,
        desc=desc,
    )
    return nadd_obj


def check_nadd_and_post_if_new(mod_info, force_submit=False, testmode=False):
    nadd_obj = get_nadd_info()
    if not force_submit:
        if nadd_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_nadd(nadd_obj, mod_info, testmode=testmode)
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
    mod_info.foundlist.append(nadd_obj.reddit_title)


def get_comment_text(nadd_obj):
    comment = ''
    comment += '"' + nadd_obj.desc + '"\n\n---\n\n###[Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_nadd(nadd_obj, mod_info, testmode=False, depth=0):
    """
    :type testmode: bool
    :type nadd_obj: NADD
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="NADD SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = 'NotAnotherDnDPodcast'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - NADD found: ", nadd_obj.reddit_title)
        return

    try:
        submission = sub.submit(nadd_obj.reddit_title, url=nadd_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        nadd_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_nadd_obj(nadd_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_nadd(nadd_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW NaddPod!!! WOOOOO!!!!")
    print(nadd_obj.reddit_title)
    post_subreddit_comment(submission, nadd_obj)
    nadd_obj.reddit_url = submission.permalink
    set_bottom_sticky(sub, submission)

    mod_info.past_history.add_nadd_obj(nadd_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, nadd_obj):
    while True:
        try:
            comment_text = get_comment_text(nadd_obj)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    nadd_obj = (get_nadd_info())
    print(nadd_obj)
    import pdb; pdb.set_trace()
    print(nadd_obj)

