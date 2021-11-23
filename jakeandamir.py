from __future__ import print_function

import re
import sys
import praw
import prawcore
import time
import warnings
import requests
import datetime

import history
import json

from jjkae_tools import replace_top_sticky, send_email, is_python_3, get_duration
import reddit_password


class JNA:
    def __init__(self, title, monthstring, url=None, reddit_title=None, reddit_url=None, desc=None, duration=None, upload_date=None):
        self.title = title
        self.monthstring = monthstring
        self.url = url
        self.reddit_title = reddit_title
        self.reddit_url = reddit_url
        self.desc = desc
        self.duration = duration
        self.upload_date = upload_date

    @classmethod
    def from_json_obj(cls, obj):
        snippet = obj['snippet']
        title = snippet['title'].split(':')[-1].strip() # ex. Podcast Ideas
        desc = snippet['description'] # ex. We're back! ...to the drawing board. \n Watch outtakes to this episode at http://www.patreon.com/JA -- plus reaction videos, podcasts, animated sketches and more!
        full_title = snippet['title']
        upload_datetime = datetime.datetime.strptime(snippet['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")

        if 'videoId' not in obj['id']:  # if, for exapmle, you're a playlist
            return None
        video_id = obj['id']['videoId']
        return cls(
            title=title,
            desc=desc.replace('\\', ''),
            monthstring=history.this_monthstring(),
            reddit_title=full_title,
            url='https://www.youtube.com/watch?v={}'.format(video_id),
            duration=get_duration(video_id),
            upload_date=upload_datetime.strftime('%b %d, %Y'),
        )

    def __repr__(self):
        return "New J&A: " + self.title

    def __str__(self):
        return self.__repr__()

def to_reddit_url(link):
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_jna_info(depth=0):
    jna_channel_id = 'UCNNxmRzlheZAeZuMYakh6vQ'
    url_fmtstring = 'https://www.googleapis.com/youtube/v3/search?key={key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=15&safeSearch=none'
    url = url_fmtstring.format(
        channel_id=jna_channel_id,
        key=reddit_password.get_yt_api_key(),
    )
    resp = requests.get(
        url,
        timeout=15.,
        headers={
            'Cache-Control': 'max-age=0, no-cache',
        }
    )
    json_data = json.loads(resp.text)
    if 'items' not in json_data:
        if depth > 5:
            send_email(subject="JSON error after 5 retries", body="json_data: {}".format(json_data), to="popcorncolonel@gmail.com")
            return None
        print("JSON ERROR?: {}".format(json_data))
        time.sleep(5)
        return get_jna_info(depth=depth+1)
    most_recent_vidz = [item for item in json_data['items'] if (
        'Jake and Amir:' in item['snippet']['title']
    )]
    jna_objs = [JNA.from_json_obj(item) for item in most_recent_vidz]
    jna_objs = [x for x in jna_objs if x]
    if jna_objs:
        return jna_objs[0]
    else:
        return None

def check_jna_and_post_if_new(mod_info, force_submit=False, testmode=False):
    jna_obj = get_jna_info()
    if jna_obj is None:
        print("GOT NONE JNA_OBJ")
        time.sleep(5)
        return check_jna_and_post_if_new(mod_info, force_submit, testmode)
    if not force_submit:
        if jna_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_jna(jna_obj, mod_info, testmode=testmode)
            append_to_episodes_txt(jna_obj, testmode=testmode)
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
    mod_info.foundlist.append(jna_obj.reddit_title)


def get_comment_text(jna_obj):
    comment = ''
    comment += '"' + jna_obj.desc + '"\n\n --- \n\n [Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_jna(jna_obj, mod_info, testmode=False, depth=0):
    """

    :type testmode: bool
    :type jna_obj: JNA
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="JNA SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        return
    subreddit = 'jakeandamir'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - jna found: ", jna_obj.reddit_title)
        return

    try:
        submission = sub.submit(jna_obj.reddit_title, url=jna_obj.url, resubmit=True)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        jna_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_jna(jna_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_jna(jna_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW JAKE AND AMIR!!! WOOOOO!!!!")
    print(jna_obj.reddit_title)
    post_subreddit_comment(submission, jna_obj)
    jna_obj.reddit_url = submission.permalink
    #submission.mod.sticky(bottom=True)
    submission.mod.distinguish()

    mod_info.past_history.add_jna(jna_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def append_to_episodes_txt(jna_obj, testmode=False):
    episodes_txt_string = "|" + "|".join([jna_obj.upload_date, jna_obj.title, jna_obj.url, "", jna_obj.duration, ""]) + "|"
    if not testmode:
        with open("episodes.txt", "a") as f:
            f.write(episodes_txt_string)
            f.write("\n")
    else:
        print("parsed episodes.txt string: '{}'".format(episodes_txt_string))


def post_subreddit_comment(submission, jna_comment):
    depth = 0
    while True:
        if depth > 3:
            return
        try:
            comment_text = get_comment_text(jna_comment)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            depth += 1
            pass
        except Exception as e:
            depth += 1
            print(e)
            pass


if __name__ == '__main__':
    jna = get_jna_info()
    print(jna)
    print(jna.duration)
    print(jna.upload_date)
    print(get_comment_text(jna))
    #append_to_episodes_txt(jna)


