from __future__ import print_function

import praw
import history
import datetime
import calendar
import reddit_password

import jjkae_tools
print(dir(jjkae_tools))
from rewatch import episodes


class ModInfo:
    def get_r(self):
        r = praw.Reddit(user_agent='JakeandAmir program by /u/popcorncolonel')
        # This makes titles that contain HTML stuff (like '&amp;') be the actual character (like '&') in unicode.
        r.config.decode_html_entities = True
        return r

    def __init__(self, next_episode, foundlist):
        self.next_episode = next_episode
        self.day = jjkae_tools.get_day()
        self.hour = jjkae_tools.get_hour()

        self.r = self.get_r()
        self.i = 1  # How many cycles the program has run for
        self.foundlist = foundlist
        self.episodes = episodes
        self.past_history = history.get_history()

        self.client_id = reddit_password.get_client_id()
        self.client_secret = reddit_password.get_client_secret()
        self.access_token = reddit_password.get_access_token()
        self.scope = reddit_password.get_scope()
        self.refresh_token = reddit_password.get_refresh_token()

    def login(self):
        #  For anyone reading this and trying to get this to run yourself: follow this tutorial: https://redd.it/3lotxj/
        #  and implement the client_id, refresh_token stuff yourself. You don't need username and password anymore.
        self.r.set_oauth_app_info(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  redirect_uri='http://127.0.0.1:65010/authorize_callback')
        access_info = {u'access_token': self.access_token,
                       u'scope': self.scope,
                       u'refresh_token': self.refresh_token}
        self.r.refresh_access_information(access_info['refresh_token'])
        self.r.set_access_credentials(**access_info)


discussion_string = '''\
Monthly discussion posts will be posted on the last weekend of every month, and subreddit rewatch episodes will be posted on the other days!

%s

Suggested topics:

* Favorite: episode, quote, or podcast.
* Least favorite: episode, quote, or podcast.
* What did you think of the latest episode or podcast?
* Any ideas or suggestions for the subreddit?
* General observations or musings.

These are just suggestions, so feel free to talk about anything that you want and discuss with others!
'''
def get_discussion_string(monthstring, past_history):
    # type: (str, History) -> str
    global discussion_string
    # Example podcast list:
    '''
    * [Episode 191: The Emotionary (w/Eden Sher!)](https://www.reddit.com/r/jakeandamir/comments/3zdczz/if_i_were_you_episode_191_the_emotionary_weden/)
    * [Episode 192: Surge Dude](https://www.reddit.com/r/jakeandamir/comments/40f0j6/if_i_were_you_episode192_surge_dude_10005/)
    '''
    added_text = ""
    if monthstring in past_history:
        if 'IIWY' in past_history[monthstring]:
            added_text += "**Podcasts released this month**:\n\n"
            for history_dict in past_history[monthstring]['IIWY']:
                added_text += "* [Episode %d: %s](%s)\n" % (history_dict['number'],
                                                            history_dict['title'],
                                                            history_dict['reddit_url'])

    return discussion_string % added_text


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

    s += '''

---

Some suggested points of discussion:

* Have you watched this series before? If so, did you pick up on anything you hadn't noticed before?
* If you haven't seen it before, what did you think?
* Favorite episode from the series?
* Favorite quotes from the episodes?
* General/misc observations
'''
    return s


def get_rewatch_string(episode):
    today_datetime = datetime.datetime.now()
    s = '''\
Welcome to the official subreddit rewatch of the Jake and Amir webseries!

Today's episode is **[{episode.title}]({episode.url})** ({episode.duration}), originally aired {episode.date_str}.'''

    if episode.bonus_footage:
        s += '\n\n**Bonus footage**: %s\n\n' % episode.bonus_footage
    s += '''

---

Some suggested points of discussion:

* Have you watched this episode before? If so, did you pick up on anything you hadn't noticed before?
* If you haven't seen it before, what did you think?
* Favorite quotes from the episode?
* General/misc observations
'''
    return s.format(date_str=today_datetime.strftime('%d'), episode=episode)


def mod_actions(mod_info, force_submit_rewatch=False, testmode=False):
    """
    If it just turned the last weekend of the month EST, post the monthly discussion.
     else, post the next subreddit rewatch (pointed to by mod_info.next_episode) and sticky it.
    """
    new_day = jjkae_tools.get_day()
    if testmode or force_submit_rewatch or new_day != mod_info.day:  # only happens on a new day at midnight
        # post discussion of the month
        if new_day in ['Saturday', 'Sunday'] and time_to_post_discussion():
            # don't post it twice (once on sunday and once on saturday - just once on the weekend)
            if new_day == 'Saturday':
                post_monthly_discussion(mod_info, testmode)
        # post rewatch episode (every day other than discussion days)
        elif new_day in ['Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']:
            post_new_rewatch(mod_info, testmode)
            mod_info.next_episode += 1

    new_hour = jjkae_tools.get_hour()
    # Run tests every hour - if any of the tests fail, email me.
    if new_hour != mod_info.hour:
        jjkae_tools.start_test_thread(email_if_failures=True)
    mod_info.day = new_day
    mod_info.hour = new_hour

def get_submission_text(mod_info, episode):
    """
    :rtype: tuple(str:title, str:submission_body)
    """
    if ',,' in episode.title:  # multipart episode
        episode_title = episode.title.split(',,')[0].split('Part')[0].split('Pt.')[0].split('pt.')[0].split('Ep.')[
            0].strip()
        title = 'Subreddit Rewatch #%d: %s (Series) (%s - %s)' % (
            mod_info.next_episode, episode_title, episode.date_str.split(',,')[0], episode.date_str.split(',,')[-1])
        return (title, get_multipart_string(episode))
    else:
        title = 'Subreddit Rewatch #%d: %s (%s)' % (mod_info.next_episode, episode.title, episode.date_str)
        return (title, get_rewatch_string(episode))

def post_new_rewatch(mod_info, testmode=False):
    sub = mod_info.r.get_subreddit('jakeandamir')
    episode = episodes[mod_info.next_episode - 1]  # next_episode is indexed by 1
    (title, text) = get_submission_text(mod_info, episode)
    if testmode:
        print("testmode - successfully parsed ep", episode.title)
        print("testmode:", title)
        return
    submission = jjkae_tools.submit(title, mod_info, 'jakeandamir', text=text)
    submission.sticky(bottom=True)
    submission.distinguish()
    sub.set_flair(submission, flair_text='REWATCH', flair_css_class='modpost')
    jjkae_tools.send_rewatch_email(submission.permalink, mod_info.next_episode)
    print("Successfully submitted sticky! Time to celebrate.")
    return submission


def post_monthly_discussion(mod_info, testmode=False):
    today_datetime = datetime.datetime.now()
    title = 'Monthly Jake and Amir Discussion (%s)' % today_datetime.strftime('%B %Y')
    if testmode:
        text = get_discussion_string(history.this_monthstring(), history.get_history())
        assert(type(text) in {str, unicode})
        return

    submission = jjkae_tools.submit(title, mod_info, 'jakeandamir',
                                    text=get_discussion_string(history.this_monthstring(), history.get_history()))
    submission.sticky(bottom=True)
    submission.distinguish()
    mod_info.set_flair(submission, flair_text='DISCUSSION POST', flair_css_class='video')
    print("Successfully submitted sticky! Time to celebrate.")
    return submission


def get_ep_num(name):
    name = name.split(" ")
    for word in name:
        if jjkae_tools.isnum(word.strip(":")):
            return int(word.strip(":"))


def time_to_post_discussion():
    dt = datetime.datetime.now()
    """ Returns true on the last weekend of the month """
    day_of_month = int(dt.strftime('%d'))
    month, year = int(dt.strftime('%m')), int(dt.strftime('%Y'))
    num_days_in_mo = calendar.monthrange(year, month)[1]
    if day_of_month >= num_days_in_mo - 7 and day_of_month != num_days_in_mo:
        return True
    else:
        return False
