from __future__ import print_function

import re
import sys
import praw
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
    if '.com' in link or '.org' in link or '.net' in link:
        link = '[' + link.split('.com')[0].split('.org')[0].split('.net')[0] + '](http://' + link.lower() + ')'
    return link

def get_iiwy_info(depth=0):
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = requests.get('https://www.spreaker.com/user/ifiwereyou', timeout=10)
        if python_3:
            soup = BeautifulSoup(''.join(r.text), "html.parser")
        else:
            soup = BeautifulSoup(''.join(r.text))
        episode_part = soup.findAll('h2', {'class': 'track_title'})[0]
        episode_part = episode_part.findAll('a')[0]
        name = episode_part.text
        title = name
        if ':' in title:  # "Episode 191: The Emotionary" -> "The Emotionary"
            title = title.split(':')[1].strip()
        url = episode_part['href']
        duration = soup.findAll('div', {'class': 'trkl_ep_duration'})[0].contents[0].strip()
        if len(duration) > 0:
            minutes = int(duration.split(':')[0])
            if minutes >= 60:
                hours = str(minutes // 60)
                minutes = '%02d' % (minutes % 60)
                duration = hours + ':' + minutes + ':' + duration.split(':')[1]
            name += ' [' + duration + ']'

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = requests.get(url, timeout=10)
            if python_3:
                soup = BeautifulSoup(''.join(r.text), "html.parser")
            else:
                soup = BeautifulSoup(''.join(r.text))
            desc = soup.findAll('div', {'class': 'track_description'})[0].contents
            desctext = desc[0].strip()
            longtext = ''.join([str(s) for s in desc])
            desc = desctext
            sponsors = longtext.split('brought to you by ')[1].strip()
            sponsorlist = get_sponsors(sponsors)
        except IndexError:
            desc = DEFAULT_STR
            sponsorlist = []
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
                    reddit_title=name, monthstring=history.this_monthstring(), url=url,
                    sponsor_list=sponsorlist, desc=desc)
    return iiwy_obj


def check_iiwy_and_post_if_new(mod_info, force_submit=False, testmode=False):
    iiwy_obj = get_iiwy_info()
    if not force_submit:
        if iiwy_obj.number in mod_info.foundlist or iiwy_obj.duration in mod_info.foundlist:  # if episode found before
            return
    while True:
        try:
            post_iiwy(iiwy_obj, mod_info, testmode=testmode)
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
    mod_info.foundlist.append(iiwy_obj.number)
    mod_info.foundlist.append(iiwy_obj.duration)


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
    sub = mod_info.r.get_subreddit(subreddit)
    mod_info.login()

    if testmode:
        print("testmode - not actually submitting anything.")
        print("testmode - IIWY found: ", iiwy_obj.reddit_title)
        return

    try:
        submission = mod_info.r.submit('jakeandamir', iiwy_obj.reddit_title, url=iiwy_obj.url)
    except praw.errors.AlreadySubmitted as e:
        print(e)
        iiwy_obj.reddit_url = 'TODO: Get the real submitted object'
        mod_info.past_history.add_iiwy(iiwy_obj)
        mod_info.past_history.write()
        return
    except Exception as e:
        print("Caught exception", e, "- recursing!")
        post_iiwy(iiwy_obj, mod_info, testmode=testmode or False, depth=depth+1)
        return
    sub.set_flair(submission, flair_text='NEW IIWY', flair_css_class='images')
    submission.approve()

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
            comment = submission.add_comment(comment_text)
            comment.approve()
            break
        except requests.exceptions.HTTPError:
            pass
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    print(get_iiwy_info())
