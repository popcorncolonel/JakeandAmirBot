from __future__ import print_function

import re
import sys
import praw
import time
import warnings
import requests

import history
import json

from jjkae_tools import replace_top_sticky, send_email, is_python_3
import reddit_password


class GTD:
    def __init__(self, number, title, monthstring, reddit_title=None, url=None, reddit_url=None, desc=None):
        self.number = number
        self.title = title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    @classmethod
    def from_json_obj(cls, obj):
        snippet = obj['snippet']
        if 'Episode' in snippet['title']:
            number = int(snippet['title'].split('Episode')[1].split()[0].strip())
            title = snippet['title'].split('-')[-1].strip()
            desc = snippet['description']
        else:
            raise ValueError('title is like {} rather than "GTD: Episode \\d\\d.'.format(snippet['title']))
        return cls(
            number=number,
            title=title,
            desc=desc.replace('\\', ''),
            monthstring=history.this_monthstring(),
            reddit_title=snippet['title'],
            url='https://www.youtube.com/watch?v={}'.format(obj['id']['videoId']),
        )

    def __repr__(self):
        return "GTD object: " + self.title

    def __str__(self):
        return self.__repr__()


def to_reddit_url(link):
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_gtd_info():
    headgum_channel_id = 'UCV58y_DbGkuYCNQC2OjJWOw'
    url_fmtstring = 'https://www.googleapis.com/youtube/v3/search?key={key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=5'
    url = url_fmtstring.format(
        channel_id=headgum_channel_id,
        key=reddit_password.get_yt_api_key(),
    )
    resp = requests.get(url)
    json_data = json.loads(resp.text)
    most_recent_vidz = [item for item in json_data['items'] if 'Geoffrey the Dumbass' in item['snippet']['title']]
    GTD_objs = [GTD.from_json_obj(item) for item in most_recent_vidz]
    if GTD_objs:
        return GTD_objs[0]
    else:
        return None

def check_gtd_and_post_if_new(mod_info, force_submit=False, testmode=False):
    gtd_obj = get_gtd_info()
    if not force_submit:
        if gtd_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_gtd(gtd_obj, mod_info, testmode=testmode)
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
    mod_info.foundlist.append(gtd_obj.reddit_title)


def get_comment_text(gtd_obj):
    comment = ''
    comment += '"' + gtd_obj.desc + '"\n\n --- \n\n [Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_gtd(gtd_obj, mod_info, testmode=False, depth=0):
    """

    :type testmode: bool
    :type gtd_obj: GTD
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="GTD SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        return
    subreddit = 'jakeandamir'
    sub = mod_info.r.get_subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - GTD found: ", gtd_obj.reddit_title)
        return

    try:
        submission = mod_info.r.submit('jakeandamir', gtd_obj.reddit_title, url=gtd_obj.url)
    except praw.errors.AlreadySubmitted as e:
        print(e)
        gtd_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_gtd(gtd_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_gtd(gtd_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    sub.set_flair(submission, flair_text='NEW GEOFFREY THE DUMBASS', flair_css_class='images')
    submission.approve()

    print("NEW GTD!!! WOOOOO!!!!")
    print(gtd_obj.reddit_title)
    post_subreddit_comment(submission, gtd_obj)
    gtd_obj.reddit_url = submission.permalink
    replace_top_sticky(sub, submission)

    mod_info.past_history.add_gtd(gtd_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, gtd_comment):
    while True:
        try:
            comment_text = get_comment_text(gtd_comment)
            comment = submission.add_comment(comment_text)
            comment.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    gtd = get_gtd_info()
    print(gtd)
    get_comment_text(gtd)
