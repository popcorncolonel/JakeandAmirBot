import sys
import time

import praw

import history
import requests
import HTMLParser

from jjkae_tools import replace_top_sticky


class LNH:
    def __init__(self, title, number, url, reddit_title, monthstring, reddit_url):
        self.title = title
        self.number = number
        self.url = url
        self.reddit_title = reddit_title
        self.monthstring = monthstring
        self.reddit_url = reddit_url

    def post(self, mod_info):
        post_lnh(self, mod_info)


def get_lnh_info(depth=0):
    monthstring = history.this_monthstring()
    lnh_obj = LNH(title="test", number=1, url='x.com', reddit_title='title',
                  monthstring=monthstring, reddit_url='reddit.com')
    return lnh_obj

def check_lnh_and_post_if_new(mod_info, force_submit=False):
    lnh_obj = get_lnh_info()
    if not force_submit:
        if ('LNH', lnh_obj.number) in mod_info.foundlist: # if episode found before
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
    mod_info.foundlist.append(('LNH', lnh_obj.number))

def post_lnh(lnh_obj, mod_info):
    subreddit = 'jakeandamir'
    sub = mod_info.r.get_subreddit(subreddit)
    mod_info.login()
    try:
        submission = mod_info.r.submit('jakeandamir', lnh_obj.reddit_title, url=lnh_obj.url)
    except praw.errors.AlreadySubmitted as e:
        print(e)
        lnh_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_iiwy(lnh_obj)
        mod_info.past_history.write()
        return
    sub.set_flair(submission, flair_text='NEW LONELY & HORNY', flair_css_class='video')
    submission.approve()

    print("NEW IIWY!!! WOOOOO!!!!")
    print(lnh_obj.reddit_title)

    lnh_obj.reddit_url = submission.permalink

    replace_top_sticky(sub, submission)

    mod_info.past_history.add_lnh(lnh_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")