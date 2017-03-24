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
    def __init__(self, number, title, monthstring, ep_type='gtd', reddit_title=None, url=None, reddit_url=None, desc=None):
        self.number = number
        self.title = title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc
        self.ep_type = ep_type

    @classmethod
    def from_json_obj(cls, obj):
        snippet = obj['snippet']
        number = None
        title = snippet['title'].split(':')[-1].strip() # ex. YoYo
        desc = snippet['description'] # ex. Geoffrey is oddly good at something, which is fine. But that's not his job. \n\n Subscribe to this channel today to make us happy!

        ep_type = None
        full_title = snippet['title']
        if 'Geoffrey the Dumbass' in full_title:
            ep_type = 'gtd'
        elif 'Off Days' in full_title:
            ep_type = 'offdays'
        if 'videoId' not in obj['id']:  # if, for exapmle, you're a playlist
            return None
        return cls(
            number=number,
            title=title,
            desc=desc.replace('\\', ''),
            monthstring=history.this_monthstring(),
            reddit_title=full_title,
            url='https://www.youtube.com/watch?v={}'.format(obj['id']['videoId']),
            ep_type=ep_type,
        )

    def __repr__(self):
        return "{} object: ".format(self.ep_type) + self.title

    def __str__(self):
        return self.__repr__()


def to_reddit_url(link):
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_gtd_info(depth=0):
    headgum_channel_id = 'UCV58y_DbGkuYCNQC2OjJWOw'
    url_fmtstring = 'https://www.googleapis.com/youtube/v3/search?key={key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=5'
    url = url_fmtstring.format(
        channel_id=headgum_channel_id,
        key=reddit_password.get_yt_api_key(),
    )
    resp = requests.get(url)
    json_data = json.loads(resp.text)
    if 'items' not in json_data:
        if depth > 5:
            send_email(subject="JSON error after 5 retries", body="json_data: {}".format(json_data), to="popcorncolonel@gmail.com")
            return None
        print("JSON ERROR?: {}".format(json_data))
        sleep(5)
        return get_gtd_info(depth=depth+1)
    most_recent_vidz = [item for item in json_data['items'] if 'Geoffrey the Dumbass' in item['snippet']['title'] or 'Off Days' in item['snippet']['title']]
    GTD_objs = [GTD.from_json_obj(item) for item in most_recent_vidz]
    GTD_objs = [x for x in GTD_objs if x]
    if GTD_objs:
        return GTD_objs[0]
    else:
        return None

def check_gtd_and_post_if_new(mod_info, force_submit=False, testmode=False):
    gtd_obj = get_gtd_info()
    if gtd_obj is None:
        print("GOT NONE GTD_OBJ")
        time.sleep(5)
        return check_gtd_and_post_if_new(mod_info, force_submit, testmode)
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
    if gtd_obj.ep_type == 'gtd':
        sub.set_flair(submission, flair_text='NEW GEOFFREY THE DUMBASS', flair_css_class='images')
    elif gtd_obj.ep_type == 'offdays':
        sub.set_flair(submission, flair_text='NEW OFF DAYS', flair_css_class='images')
    submission.approve()

    print("NEW GTD/OD!!! WOOOOO!!!!")
    print(gtd_obj.reddit_title)
    post_subreddit_comment(submission, gtd_obj)
    gtd_obj.reddit_url = submission.permalink
    submission.sticky(bottom=True)
    #replace_top_sticky(sub, submission)
    submission.distinguish()

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
