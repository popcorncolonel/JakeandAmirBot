from __future__ import print_function

import re
import sys
import time

import praw

import history
import requests
import HTMLParser

from jjkae_tools import replace_top_sticky

html_parser = HTMLParser.HTMLParser()

python_3 = False
if sys.version_info >= (3, 0):
    python_3 = True
    from bs4 import BeautifulSoup
else:
    from BeautifulSoup import BeautifulSoup


class LNH:
    def __init__(self, titles, urls, reddit_title, monthstring, duration, reddit_url=None, desc=None):
        self.titles = titles
        self.urls = urls
        self.reddit_title = reddit_title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.duration = duration
        self.desc = desc

    def post(self, mod_info):
        post_lnh(self, mod_info)

    def __repr__(self):
        return "LNH submission object: {0}".format(self.titles)

    def __str__(self):
        return self.__repr__()


def get_lnh_info(depth=0):
    # type: (int) -> LNH
    monthstring = history.this_monthstring()

    r = requests.get('https://vimeo.com/ondemand/lonelyandhorny', timeout=10)
    html_body = r.text

    # Parse most recent episode info

    if python_3:
        soup = BeautifulSoup(''.join(r.text), "html.parser")
    else:
        soup = BeautifulSoup(''.join(r.text))
    episode_part = soup.findAll('a', {'data-detail-url': re.compile('.*')})[0]
    name = episode_part['title']  # "E=mc2"
    url = episode_part['href']  # /ondemand/lonelyandhorny/<ID>
    url = 'https://vimeo.com' + url
    duration = soup.findAll('time')[0].contents[0]  # "08:46"

    # TODO: Get most recent and second most recent, return a tuple. (not the first and second episodes)

    reddit_title = 'title'
    reddit_title = html_parser.unescape(reddit_title)
    lnh_url = url
    lnh_url = html_parser.unescape(lnh_url)
    lnh_urls = (lnh_url,)

    title = name
    title = html_parser.unescape(title)

    titles = (title,)

    desc = 'i hope u like the show'

    lnh_obj = LNH(titles=titles, urls=lnh_urls, reddit_title=reddit_title, monthstring=monthstring, duration=duration, desc=desc)
    return lnh_obj


def check_lnh_and_post_if_new(mod_info, force_submit=False):
    lnh_obj = get_lnh_info()
    if not force_submit:
        if ('LNH', lnh_obj.titles) in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            lnh_obj.post(mod_info)
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
    mod_info.foundlist.append(('LNH', lnh_obj.titles))


def post_lnh(lnh_obj, mod_info):
    """

    :type mod_info: ModInfo
    :type lnh_obj: LNH
    """
    subreddit = 'jakeandamir'
    sub = mod_info.r.get_subreddit(subreddit)
    mod_info.login()
    try:
        submission = mod_info.r.submit('jakeandamir', lnh_obj.reddit_title, text=lnh_obj.desc)
    except praw.errors.AlreadySubmitted as e:
        print(e)
        lnh_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_lnh(lnh_obj)
        mod_info.past_history.write()
        return
    sub.set_flair(submission, flair_text='NEW LONELY & HORNY', flair_css_class='video')
    submission.approve()

    print("NEW LNH!!! WOOOOO!!!!")
    print(lnh_obj.reddit_title)

    lnh_obj.reddit_url = submission.permalink

    replace_top_sticky(sub, submission)

    mod_info.past_history.add_lnh(lnh_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")


def get_comment_text(lnh_obj):
    return ':)'


def post_subreddit_comment(submission, lnh_obj):
    while True:
        try:
            comment_text = get_comment_text(lnh_obj)
            comment = submission.add_comment(comment_text)
            comment.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    print(get_lnh_info())
