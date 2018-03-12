from __future__ import print_function

import re
import sys
import json
import praw
import prawcore
import time
import warnings
import requests

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
    def __init__(self, title, duration, monthstring,
                 number=None, reddit_title=None, url=None, reddit_url=None, desc=None):
        self.number = number
        self.title = title
        self.duration = duration
        self.monthstring = monthstring
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
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            naddpod_id = 'ef988f11-5f99-486e-8e7f-cf789aafa720'
            r = requests.get(
                'https://art19.com/episodes?series_id={}&sort=created_at'.format(naddpod_id),
                headers={'Accept': 'application/vnd.api+json', 'Authorization': 'token="test-token", credential="test-credential"'},
                timeout=15.0,
            )
            j = json.loads(r.text)
            most_recent_ep = j['data'][-1]['attributes']
            most_recent_ep_id = j['data'][-1]['id']
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
    orig_title = most_recent_ep['title']  # full title including number. `title` is like "Ep. 5: Dark Ritual (The Moonstone Saga)"
    url = 'https://art19.com/shows/not-another-d-and-d-podcast/episodes/{}'.format(most_recent_ep_id)
    """
    duration_secs = most_recent_ep['duration'] // 1000
    if duration_secs < 3600:
        duration = '{:02d}:{:02d}'.format(duration_secs // 60, duration_secs % 60)
    else:
        duration = '{}:{:02d}:{:02d}'.format(duration_secs // 3600, (duration_secs % 3600) // 60, duration_secs % 60)
    """
    duration = None
    episode_num = None
    title = orig_title
    if ': ' in orig_title:
        [episode_num, title] = orig_title.split(': ', maxsplit=1)  # now `title` is like "Dark Ritual (The Moonstone Saga)"
        episode_num_string = episode_num.split(' ')[-1]  # Ep. 5 -> 5, 'BONUS EPISODE' -> 'EPISODE'
        if episode_num_string.isdigit():
            episode_num = int(episode_num_string)
    if duration is not None:
        name = 'Episode {episode_num}: {title} [{duration}]'.format(**locals())
    elif episode_num is not None:
        name = 'Episode {episode_num}: {title}'.format(**locals())
    else:
        name = 'Not Another D&D Podcast: {orig_title}'.format(**locals())
    reddit_title = name
    desc = most_recent_ep['description']
    desc = re.sub('<.*?>', '\n', desc).replace('  ', ' ').replace('  ', ' ')  # replace <br> with \n, prevent weird space formatting i guess?

    desc = desc.replace('"', "'").strip()
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    nadd_obj = NADD(
        number=episode_num,
        title=title,
        duration=duration,
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
    #submission.mod.approve()

    print("NEW NaddPod!!! WOOOOO!!!!")
    print(nadd_obj.reddit_title)
    post_subreddit_comment(submission, nadd_obj)
    nadd_obj.reddit_url = submission.permalink
    #set_bottom_sticky(sub, submission)

    mod_info.past_history.add_nadd_obj(nadd_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, nadd_obj):
    while True:
        try:
            comment_text = get_comment_text(nadd_obj)
            comment = submission.reply(comment_text)
            #comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    nadd_obj = (get_nadd_info())
    import pdb; pdb.set_trace()
    print(nadd_obj)

