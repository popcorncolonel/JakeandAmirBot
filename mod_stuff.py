import history
from jjkae_tools import send_emails, isnum
from rewatch import episodes
import datetime

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
def get_discussion_string(monthstring):
    global discussion_string, past_history
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
                added_text += "* [Episode %d: %s](%s)\n" %(history_dict['number'],
                                                           history_dict['title'],
                                                           history_dict['reddit_url'])

    return discussion_string % added_text


def get_multipart_string(episode):
    s = '''\
Welcome to the official subreddit rewatch of the Jake and Amir webseries!

Today's episodes are a multi-part series! The episodes in this series are:\n\n'''
    titles = episode.title.split(',,')
    urls = episode.url.split(',,')
    durations = episode.duration.split(',,')
    dates = episode.date_str.split(',,')
    for (title, url, duration, date_str) in zip(titles, urls, durations, dates):
        s += '* **[%s](%s)** (%s), originally aired %s.  \n' %(title, url, duration, date_str)

    if episode.bonus_footage:
        s += '\n\n**Bonus footage**: %s' %episode.bonus_footage

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


def mod_actions(next_episode, debug, r, user, paw, day):
    '''
    If it just turned the last weekend of the month EST, post the monthly discussion.
     else, post the next subreddit rewatch (pointed to by next_episode) and sticky it.
    '''

    subreddit_name = 'jakeandamir'
    sub = r.get_subreddit(subreddit_name)

    today_datetime = datetime.datetime.now()
    new_day = today_datetime.strftime('%A')
    if new_day != day: # on a new day at midnight
        if new_day in ['Saturday', 'Sunday'] and time_to_post_discussion(today_datetime): # post discussion of the month
            if new_day == 'Saturday': # don't post it twice (once on sunday and once on saturday - just once on the weekend)
                title = 'Monthly Jake and Amir Discussion (%s)' % today_datetime.strftime('%B %Y')
                submission = submit(title, text=get_discussion_string(history.this_monthstring()))
                submission.sticky(bottom=True)
                submission.distinguish()
                sub.set_flair(submission, flair_text='DISCUSSION POST', flair_css_class='video')
                print("Successfully submitted sticky! Time to celebrate.")
        # post rewatch episode (every day other than discussion days)
        elif new_day in ['Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']:
        #elif new_day in []:
            episode = episodes[next_episode-1] # next_episode is indexed by 1
            if ',,' in episode.title: # multipart episode
                episode_title = episode.title.split(',,')[0].split('Part')[0].split('Pt.')[0].split('pt.')[0].split('Ep.')[0].strip()
                title = 'Subreddit Rewatch #%d: %s (Series) (%s - %s)' %(next_episode, episode_title, episode.date_str.split(',,')[0], episode.date_str.split(',,')[-1])
                submission = submit(title, text=get_multipart_string(episode))
            else:
                title = 'Subreddit Rewatch #%d: %s (%s)' %(next_episode, episode.title, episode.date_str)
                submission = submit(title, text=get_rewatch_string(episode))
            submission.sticky(bottom=True)
            submission.distinguish()
            sub.set_flair(submission, flair_text='REWATCH', flair_css_class='modpost')
            send_emails(submission.permalink)
            print("Successfully submitted sticky! Time to celebrate.")
            next_episode += 1



def get_ep_num(name):
    name = name.split(" ")
    for word in name:
        if isnum(word.strip(":")):
            return int(word.strip(":"))


def time_to_post_discussion(dt):
    ''' returns true on the last weekend of the month '''
    day_of_month = int(dt.strftime('%d'))
    month, year = int(dt.strftime('%m')), int(dt.strftime('%Y'))
    num_days_in_mo = calendar.monthrange(year, month)[1]
    if day_of_month >= num_days_in_mo - 7 and day_of_month != num_days_in_mo:
        return True
    else:
        return False


def submit(title, text=None, url=None):
    '''
    Submits the relevant information to the subreddit
    '''
    global r, user, paw, subreddit
    while True:
        try:
            r.login(user, paw)
            if text:
                return r.submit(subreddit, title, text=text, resubmit=True)
            elif url:
                return r.submit(subreddit, title, url=url)
            else:
                raise ValueError('No self-text or url specified')
        except requests.exceptions.HTTPError as e:
            print("had trouble submitting D: HTTPError.")
            print(e)
            time.sleep(3)
            pass
        except Exception as e:
            print("had trouble submitting D:")
            print("Exception:", str(e))
            time.sleep(3)
            pass


