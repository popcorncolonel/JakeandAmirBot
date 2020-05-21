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


class Revue:
    def __init__(self, title, monthstring,
                 reddit_title=None, url=None, reddit_url=None, desc=None):
        self.title = title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "ReviewRevue submission object: " + self.title

    def __str__(self):
        return self.__repr__()


def get_revue_info(depth=0):
    title = None
    name = None
    url = None
    desc = None
    filename = None
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            '''
            Note to self for the future on how to get this:
            shoot a little GET request over to https://art19.com/series?q=review-revue.
            Doing it in Python is the easiest, you can just do the one-liner:
            requests.get('https://art19.com/series?q=review-revue',headers={'Accept': 'application/vnd.api+json', 'Authorization': 'token="test-token", credential="test-credential"'})
            '''
            revue_id = '629ca490-23d2-48dd-9bd1-c173ef8a58ec'
            r = requests.get(
                'https://art19.com/episodes?series_id={}&sort=-created_at&page[number]=1&page[size]=10'.format(revue_id),
                headers={'Accept': 'application/vnd.api+json', 'Authorization': 'token="test-token", credential="test-credential"'},
                timeout=15.0,
            )
            j = json.loads(r.text)
            most_recent_ep = j['data'][0]['attributes']
            most_recent_ep_id = j['data'][0]['id']
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered request Timeout. recursing.")
        time.sleep(3)
        return get_revue_info()
    except Exception as e:
        print("encountered request error =(")
        print(e)
        time.sleep(3)
        return get_revue_info(depth=depth + 1)
    title = most_recent_ep['title']  # Full title, that's it. `title` is like "Beginner Guitars"
    url = 'https://art19.com/shows/review-revue/episodes/{}'.format(most_recent_ep_id)
    name = 'Review Revue: {title}'.format(**locals())
    reddit_title = name
    desc = most_recent_ep['description']
    desc = re.sub('<.*?>', '\n', desc).replace('  ', ' ').replace('  ', ' ')  # replace <br> with \n, prevent weird space formatting i guess?

    desc = desc.replace('"', "'").strip()
    desc = desc.split('\n\n')[0]
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    revue_obj = Revue(
        title=title,
        reddit_title=reddit_title,
        monthstring=history.this_monthstring(),
        url=url,
        desc=desc,
    )
    return revue_obj


def check_revue_and_post_if_new(mod_info, force_submit=False, testmode=False):
    revue_obj = get_revue_info()
    if not force_submit:
        if revue_obj.reddit_title in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_revue(revue_obj, mod_info, testmode=testmode)
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
    mod_info.foundlist.append(revue_obj.reddit_title)


def get_comment_text(revue_obj):
    comment = ''
    comment += '"' + revue_obj.desc + '"\n\n---\n\n###[Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    return comment


def post_revue(revue_obj, mod_info, testmode=False, depth=0):
    """
    :type testmode: bool
    :type revue_obj: Revue
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="REVUE SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = 'ReviewRevue'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - Revue found: ", revue_obj.reddit_title)
        return

    try:
        submission = sub.submit(revue_obj.reddit_title, url=revue_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        revue_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_revue_obj(revue_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_revue(revue_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW ReviewRevue!!! WOOOOO!!!!")
    print(revue_obj.reddit_title)
    post_subreddit_comment(submission, revue_obj)
    revue_obj.reddit_url = submission.permalink
    set_bottom_sticky(sub, submission)

    mod_info.past_history.add_revue_obj(revue_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, revue_obj):
    while True:
        try:
            comment_text = get_comment_text(revue_obj)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    revue_obj = get_revue_info()
    import pdb; pdb.set_trace()
    print(revue_obj)

