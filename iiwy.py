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

from jjkae_tools import replace_top_sticky, send_email, is_python_3

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


class IIWY:
    def __init__(self, number, title, duration, monthstring, sponsor_list, reddit_title=None, url=None, reddit_url=None,
                 desc=None):
        self.number = number
        self.title = title
        self.duration = duration
        self.monthstring = monthstring
        self.sponsor_list = sponsor_list
        self.reddit_url = reddit_url
        self.reddit_title = reddit_title
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "IIWY submission object: " + self.title

    def __str__(self):
        return self.__repr__()



def get_sponsors(sponsors):
    sponsorlist = []
    if ',' in sponsors:  # Squarespace.com, MeUndies.com, and DollarShaveClub.com!
        csvs = sponsors.split(',')
        if len(csvs) == 3:
            sponsorlist.append(csvs[0].strip())
            sponsorlist.append(csvs[1].strip())
            sponsorlist.append(csvs[2].split('and')[1].strip().rstrip('.').rstrip('!'))
        elif len(csvs) == 4:
            sponsorlist.append(csvs[0].strip())
            sponsorlist.append(csvs[1].strip())
            sponsorlist.append(csvs[2].strip())
            sponsorlist.append(csvs[3].split('and')[1].strip().rstrip('.').rstrip('!'))
    elif ' and ' in sponsors:  # Squarespace.com and DollarShaveClub.com
        sponsorlist.append(sponsors.split(' and ')[0].strip())
        sponsorlist.append(sponsors.split(' and ')[1].strip().rstrip('.').rstrip('!'))
    else:  # MeUndies.com
        sponsorlist.append(sponsors.strip().rstrip('.').rstrip('!'))
    return sponsorlist


def to_reddit_url(link):
    '''
    Turns "google.com" into "[google](google.com)"
    '''
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_iiwy_info(depth=0):
    title = None
    name = None
    url = None
    desc = None
    sponsorlist = None
    episode_num = None
    filename = None
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # ART19 HAS A TERRIBLE API
            r = requests.get(
                'https://art19.com/episodes?series_id=92b3b85d-6ac4-49b1-88fa-44328c4a69e1&sort=created_at',
                headers={'Accept': 'application/vnd.api+json', 'Authorization': 'token="test-token", credential="test-credential"'},
                timeout=15.0,
            )
            j = json.loads(r.text)
            most_recent_ep = j['data'][-1]['attributes']
            most_recent_ep_id = j['data'][-1]['id']
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print("encountered spreaker Timeout. recursing.")
        time.sleep(3)
        return get_iiwy_info()
    except Exception as e:
        print("encountered spreaker error =(")
        print(e)
        time.sleep(3)
        return get_iiwy_info(depth=depth + 1)
    name = most_recent_ep['title']  # name is the full title. `title` is like "The Emotionary"
    if ':' in name:  # "Episode 191: The Emotionary" -> "The Emotionary"
        title = name.split(':')[1].strip()
    else:
        title = name
    url = 'https://art19.com/shows/if-i-were-you/episodes/{}'.format(most_recent_ep_id)
    duration = None
    ''' Art19 does not provide support for duration!!!
    duration = soup.findAll('div', {'class': 'trkl_ep_duration'})[0].contents[0].strip()
    if len(duration) > 0:
        minutes = int(duration.split(':')[0])
        if minutes >= 60:
            hours = str(minutes // 60)
            minutes = '%02d' % (minutes % 60)
            duration = hours + ':' + minutes + ':' + duration.split(':')[1]
        name += ' [' + duration + ']'
    '''
    reddit_title = name

    sponsorlist = []
    desc = most_recent_ep['description']
    desc = re.sub('<.*?>', '', desc).replace('  ', ' ').replace('  ', ' ')
    filename = most_recent_ep['file_name']  # lol why is this information included
    ''' temporarily disabled...
    if 'brought to you by ' in desc:
        sponsors = desc.split('brought to you by ')[1].strip()
        sponsorlist = get_sponsors(sponsors)
    '''
    episode_num = re.search('\d+', name.split(':')[0].split('Episode')[1].strip()).group()
    episode_num = int(episode_num)
    try:
        if 'If I Were You' not in name:
            name = "If I Were You " + name
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print("encountered iiwy error :((((")
        print(e)
        time.sleep(3)

    sponsorlist = list(map(to_reddit_url, sponsorlist))
    desc = desc.replace('"', "'").strip()
    name = html_parser.unescape(name)
    title = html_parser.unescape(title)
    desc = html_parser.unescape(desc)
    iiwy_obj = IIWY(number=episode_num, title=title, duration=duration,
                    reddit_title=reddit_title, monthstring=history.this_monthstring(), url=url,
                    sponsor_list=sponsorlist, desc=desc)
    return iiwy_obj


def check_iiwy_and_post_if_new(mod_info, force_submit=False, testmode=False):
    iiwy_obj = get_iiwy_info()
    if not force_submit:
        if iiwy_obj.number in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_iiwy(iiwy_obj, mod_info, testmode=testmode)
            break
        except requests.exceptions.HTTPError:
            print("HTTP error while trying to submit - retrying to resubmit")
            pass
        except Exception as e:
            print("Error", e)
            break
    mod_info.foundlist.append(iiwy_obj.number)
    #mod_info.foundlist.append(iiwy_obj.duration)


def get_comment_text(iiwy_obj):
    comment = ''
    comment += '"' + iiwy_obj.desc + '"\n\n---\n\n###Links\n\n [If I Were You Bingo](http://iiwybingo.appspot.com)\n\n [Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
    if iiwy_obj.sponsor_list != []:
        n_sponsors = len(iiwy_obj.sponsor_list)
        comment += '\n\n This episode\'s sponsors: '
        if n_sponsors == 1:
            comment += iiwy_obj.sponsor_list[0]
        elif n_sponsors == 2:
            comment += iiwy_obj.sponsor_list[0] + ' and ' + iiwy_obj.sponsor_list[1]
        elif n_sponsors == 3:
            comment += (iiwy_obj.sponsor_list[0] + ', ' +
                        iiwy_obj.sponsor_list[1] + ', and ' +
                        iiwy_obj.sponsor_list[2])
        elif n_sponsors == 4:
            comment += (iiwy_obj.sponsor_list[0] + ', ' +
                        iiwy_obj.sponsor_list[1] + ', ' +
                        iiwy_obj.sponsor_list[2] + ', and ' +
                        iiwy_obj.sponsor_list[3])
    return comment


def post_iiwy(iiwy_obj, mod_info, testmode=False, depth=0):
    """

    :type testmode: bool
    :type iiwy_obj: IIWY
    :type mod_info: ModInfo
    """
    if depth > 3:
        send_email(subject="IIWY SUBMISSION ERROR", body="IDK", to="popcorncolonel@gmail.com")
        sys.exit() # should I exit or just keep going???
    subreddit = 'jakeandamir'
    sub = mod_info.r.subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - IIWY found: ", iiwy_obj.reddit_title)
        return

    try:
        submission = sub.submit(iiwy_obj.reddit_title, url=iiwy_obj.url)
    except prawcore.exceptions.ServerError as e:
        print("Already submitted?")
        print(e)
        iiwy_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_iiwy(iiwy_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_iiwy(iiwy_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    submission.mod.approve()

    print("NEW IIWY!!! WOOOOO!!!!")
    print(iiwy_obj.reddit_title)
    post_subreddit_comment(submission, iiwy_obj)
    iiwy_obj.reddit_url = submission.permalink
    replace_top_sticky(sub, submission)

    mod_info.past_history.add_iiwy(iiwy_obj)
    mod_info.past_history.write()
    print("Successfully submitted link! Time to celebrate.")
    return submission


def post_subreddit_comment(submission, iiwy_obj):
    while True:
        try:
            comment_text = get_comment_text(iiwy_obj)
            comment = submission.reply(comment_text)
            comment.mod.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    iiwy_obj = (get_iiwy_info())
    import pdb; pdb.set_trace()
    print(iiwy_obj)
