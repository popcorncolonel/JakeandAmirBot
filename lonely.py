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
    def __init__(self, titles, urls, reddit_title, monthstring, durations, reddit_url=None, desc=None):
        self.titles = titles
        self.urls = urls
        self.reddit_title = reddit_title
        self.monthstring = monthstring
        self.reddit_url = reddit_url
        self.durations = durations
        self.desc = desc

    def post(self, mod_info):
        post_lnh(self, mod_info)

    def __repr__(self):
        return "LNH submission object: {0}".format(self.titles)

    def __str__(self):
        return self.__repr__()


def get_title(link_tag):
    return link_tag['title']


def get_url(link_tag):
    url = link_tag['href']  # /ondemand/lonelyandhorny/<ID>
    url = 'https://vimeo.com' + url
    return url


def get_duration(time_tag):
    duration = time_tag.contents[0]  # "08:46"
    if ':' in duration:
        d = duration.split(':')
        duration = str(int(d[0])) + ":" + d[1]
    return duration

desc_string = '''\
New Lonely & Horny episodes!

* [{t1} ({dur1})]({url1})
* [{t2} ({dur2})]({url2})
'''
def get_lnh_desc_body(lnh_obj):
    """

    :rtype: str
    :type lnh_obj: LNH
    """
    global desc_string
    title1 = lnh_obj.titles[0]
    duration1 = lnh_obj.durations[0]
    url1 = lnh_obj.urls[0]

    title2 = lnh_obj.titles[1]
    duration2 = lnh_obj.durations[1]
    url2 = lnh_obj.urls[1]
    desc = desc_string.format(
        t1=title1, dur1=duration1, url1=url1,
        t2=title2, dur2=duration2, url2=url2)
    return desc


def get_lnh_info():
    # type: (int) -> LNH
    """

    :rtype: LNH
    """
    # Get most recent and second most recent, return a tuple. (not the first and second episodes)
    monthstring = history.this_monthstring()

    r = requests.get('https://vimeo.com/ondemand/lonelyandhorny', timeout=10)
    html_body = r.text

    # Parse most recent episode info

    if python_3:
        soup = BeautifulSoup(''.join(html_body), "html.parser")
    else:
        soup = BeautifulSoup(''.join(html_body))
    link_tags = soup.findAll('a', {'data-detail-url': re.compile('.*')})
    time_tags = soup.findAll('time')

    link_tag_1 = link_tags[-2]
    name1 = get_title(link_tag_1)  # "E=mc2"
    url1 = get_url(link_tag_1)  # https://vimeo.com/ondemand/lonelyandhorny/<ID>
    duration1 = get_duration(time_tags[-2])

    link_tag_2 = link_tags[-1]
    name2 = get_title(link_tag_2)  # "Orion"
    url2 = get_url(link_tag_2)  # https://vimeo.com/ondemand/lonelyandhorny/<ID>
    duration2 = get_duration(time_tags[-1])

    url1 = html_parser.unescape(url1)
    url2 = html_parser.unescape(url2)
    lnh_urls = (url1, url2)

    title1 = name1
    title1 = html_parser.unescape(title1)
    title2 = name2
    title2 = html_parser.unescape(title2)

    titles = (title1, title2)

    durations = (duration1,duration2)

    reddit_title = 'Lonely & Horny Discussion Post: {t1} & {t2}'.format(
                t1=title1, dur1=duration1,
                t2=title2, dur2=duration2)
    reddit_title = html_parser.unescape(reddit_title)
    print(reddit_title)


    lnh_obj = LNH(titles=titles, urls=lnh_urls, reddit_title=reddit_title, monthstring=monthstring, durations=durations)

    desc = get_lnh_desc_body(lnh_obj)
    lnh_obj.desc = desc
    return lnh_obj


def check_lnh_and_post_if_new(mod_info, force_submit=False):
    lnh_obj = get_lnh_info()
    if not force_submit:
        if all([('LNH', title) not in mod_info.foundlist for title in lnh_obj.titles]):
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
    for title in lnh_obj.titles:
        mod_info.foundlist.append(('LNH', title))


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
