from __future__ import print_function

import re
import sys
import praw
import prawcore
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
        elif 'Day in the Strife' in full_title:
            ep_type = 'dayinthestrife'
        elif 'Jake and Amir:' in full_title:
            ep_type = 'jna'
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
        return "{} object: ".format(self.ep_type) + self.title + '|' + self.reddit_title + '|' + self.url

    def __str__(self):
        return self.__repr__()


def to_reddit_url(link):
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_gtd_info(depth=0, topN=1):
    '''
        topN: get the most recent N GtD's
    '''
    headgum_channel_id = 'UCV58y_DbGkuYCNQC2OjJWOw'
    url_fmtstring = 'https://www.googleapis.com/youtube/v3/search?key={key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=50&safeSearch=none&publishedAfter=2024-01-01T00:00:00Z'
    url = url_fmtstring.format(
        channel_id=headgum_channel_id,
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
        return get_gtd_info(depth=depth+1)
    most_recent_vidz = [item for item in json_data['items'] if (
        'Jake and Amir:' in item['snippet']['title'] or
        'Day in the Strife' in item['snippet']['title'] or
        'Off Days' in item['snippet']['title'] or 
        'Geoffrey the Dumbass' in item['snippet']['title']
    )]
    GTD_objs = [GTD.from_json_obj(item) for item in most_recent_vidz]
    GTD_objs = [x for x in GTD_objs if x]
    if GTD_objs:
        if topN > 1:
            return GTD_objs[:topN]
        else:
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
        except prawcore.exceptions.ServerError:
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
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - GTD found: ", gtd_obj.reddit_title)
        return

    try:
        if gtd_obj.ep_type in ['gtd', 'offdays', 'dayinthestrife', 'jna']:
            #submission = sub.submit(gtd_obj.reddit_title, url=gtd_obj.url, flair_text='NEW GEOFFREY THE DUMBASS', flair_id='images')
            submission = sub.submit(gtd_obj.reddit_title, url=gtd_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        gtd_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_gtd(gtd_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_gtd(gtd_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW GTD/OD!!! WOOOOO!!!!")
    print(gtd_obj.reddit_title)
    post_subreddit_comment(submission, gtd_obj)
    gtd_obj.reddit_url = submission.permalink
    #submission.mod.sticky(bottom=True)
    #replace_top_sticky(sub, submission)
    #submission.mod.distinguish()

    mod_info.past_history.add_gtd(gtd_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, gtd_comment):
    depth = 0
    while True:
        if depth > 3:
            return
        try:
            comment_text = get_comment_text(gtd_comment)
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
    gtd = get_gtd_info()
    print(gtd)
    print(gtd.reddit_title)
    print(get_comment_text(gtd))

    gtds = get_gtd_info(topN=50)
    print(gtds)
    print("{} videos found out of 25".format(len(gtds)))

