from __future__ import print_function

import praw
import history
import datetime
import calendar
import reddit_password
import random

import jjkae_tools
from rewatch import episodes


class ModInfo:
    def get_r(self):
        r = praw.Reddit(
            user_agent='JakeandAmir program by /u/popcorncolonel',
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=self.refresh_token,
        )
        # This makes titles that contain HTML stuff (like '&amp;') be the actual character (like '&') in unicode.
        r.config.decode_html_entities = True
        return r

    def __init__(self, foundlist):
        self.client_id = reddit_password.get_client_id()
        self.client_secret = reddit_password.get_client_secret()
        self.access_token = reddit_password.get_access_token()
        self.scope = reddit_password.get_scope()
        self.refresh_token = reddit_password.get_refresh_token()

        self.day = jjkae_tools.get_day()
        self.hour = jjkae_tools.get_hour()

        self.r = self.get_r()
        self.i = 1  # How many cycles the program has run for
        self.foundlist = foundlist
        self.episodes = episodes
        self.past_history = history.get_history()

    def login(self):
        #  For anyone reading this and trying to get this to run yourself: follow this tutorial: https://redd.it/3lotxj/
        #  and implement the client_id, refresh_token stuff yourself. You don't need username and password anymore.
        '''
        self.r.set_oauth_app_info(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  redirect_uri='http://127.0.0.1:65010/authorize_callback')
        access_info = {u'access_token': self.access_token,
                       u'scope': self.scope,
                       u'refresh_token': self.refresh_token}
        self.r.refresh_access_information(access_info['refresh_token'])
        self.r.set_access_credentials(**access_info)
        '''
        pass


def get_multipart_string(episode):
    # type: Episode -> str
    s = '''\
Welcome to the official subreddit rewatch of the Jake and Amir webseries!

Today's episodes are a multi-part series! The episodes in this series are:\n\n'''
    titles = episode.title.split(',,')
    urls = episode.url.split(',,')
    durations = episode.duration.split(',,')
    dates = episode.date_str.split(',,')
    for (title, url, duration, date_str) in zip(titles, urls, durations, dates):
        s += '* **[%s](%s)** (%s), originally aired %s.  \n' % (title, url, duration, date_str)

    if episode.bonus_footage:
        s += '\n\n**Bonus footage**: %s' % episode.bonus_footage

    return s


def get_rewatch_string(episode):
    today_datetime = datetime.datetime.now()
    s = '''\
Welcome to the official subreddit rewatch of the Jake and Amir webseries!

Today's episode is **[{episode.title}]({episode.url})** ({episode.duration}), originally aired {episode.date_str}.'''

    if episode.bonus_footage:
        s += '\n\n**Bonus footage**: %s\n\n' % episode.bonus_footage
    return s.format(date_str=today_datetime.strftime('%d'), episode=episode)


def mod_actions(mod_info, force_submit_rewatch=False, testmode=False):
    """
    Post the next subreddit rewatch (random.choice(episodes)) and sticky it.
    """
    new_day = jjkae_tools.get_day()
    new_hour = jjkae_tools.get_hour()
    # Run tests every hour - if any of the tests fail, email me.
    rewatch_days = {'Monday', 'Friday'}
    if force_submit_rewatch or testmode or new_hour != mod_info.hour:
        if force_submit_rewatch or testmode or (new_day in rewatch_days and int(new_hour) == 8):  # if it turns to be 8am, post the rewatch!
            post_new_rewatch(mod_info, testmode)
    mod_info.day = new_day
    mod_info.hour = new_hour

def get_submission_text(mod_info, episode):
    """
    :rtype: tuple(str:title, str:submission_body, str:episode_title)
    """
    episode_title = episode.title
    if ',,' in episode.title:  # multipart episode
        episode_title = episode.title.split(',,')[0].split('Part')[0].split('Pt.')[0].split('pt.')[0].split('Ep.')[
            0].strip()
        title = 'Jake and Amir: %s (Series)' % (episode_title)
        return (title, get_multipart_string(episode), episode_title)
    else:
        title = 'Jake and Amir: %s' % (episode.title)
        return (title, get_rewatch_string(episode), episode_title)

def post_new_rewatch(mod_info, testmode=False):
    sub = mod_info.r.subreddit('jakeandamir')
    episode = random.choice(episodes)
    (title, text, episode_title) = get_submission_text(mod_info, episode)
    if testmode:
        print("testmode - successfully parsed rewatch ep", episode.title)
        print("testmode:", title)
        print("testmode:", episode_title)
        return
    submission = jjkae_tools.submit(title, mod_info, sub, text=text)
    jjkae_tools.set_bottom_sticky(sub, submission)
    #sub.set_flair(submission, flair_text='REWATCH', flair_css_class='modpost')
    for flair_dict in submission.flair.choices():
        if flair_dict['flair_text'] == 'REWATCH':
            submission.flair.select(flair_dict['flair_template_id'])
    jjkae_tools.send_rewatch_email("https://reddit.com{}".format(submission.permalink), episode_title)
    print("Successfully submitted rewatch! Time to celebrate.")
    return submission


def get_ep_num(name):
    name = name.split(" ")
    for word in name:
        if jjkae_tools.isnum(word.strip(":")):
            return int(word.strip(":"))


