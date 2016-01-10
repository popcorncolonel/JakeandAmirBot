import re
import sys
import time
import iiwy
import history
import urllib.request, urllib.error, urllib.parse
import requests
import datetime
import calendar
import warnings
import webbrowser
import html.parser

from rewatch import episodes
python_3 = False
if sys.version_info >= (3, 0):
    python_3 = True
    from bs4 import BeautifulSoup
else:
    from BeautifulSoup import BeautifulSoup

# have to create a reddit_password.py file with a get_password() function
import reddit_password

open_in_browser = False

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import praw

DEFAULT_STR = ''
debug = False

r = praw.Reddit(user_agent = 'JakeandAmir program by /u/popcorncolonel')
user = 'JakeandAmirBot'
paw = reddit_password.get_password()
subreddit = 'jakeandamir'

sub = r.get_subreddit(subreddit)
r.config.decode_html_entities = True

next_episode = -1 # START AT 1
if len(sys.argv) > 1:
    next_episode = int(sys.argv[1])

if next_episode > -1:
    print('Previous episode:', episodes[next_episode-2])
    print('Next episode to be posted:', episodes[next_episode-1])
    time.sleep(3)

timeout = default_timeout = 5 #don't spam the servers :D

past_history = history.get_history()

def isnum(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def get_ep_num(name):
    name = name.split(" ")
    for word in name:
        if isnum(word.strip(":")):
            return int(word.strip(":"))
 

#submits the relevant information to the subreddit
def submit(title, text=None, url=None):
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

def get_comment_text(iiwy_obj):
    comment = ''
    comment += '"'+iiwy_obj.desc+'"\n\n---\n\n###Links\n\n [If I Were You Bingo](http://iiwybingo.appspot.com)\n\n [Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
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

def post_iiwy(iiwy_obj):
    global past_history
    if open_in_browser:
        webbrowser.open(iiwy_obj.url)
    r.login(user, paw)
    try:
        submission = r.submit(subreddit, iiwy_obj.title, url=iiwy_obj.url)
    except praw.errors.AlreadySubmitted as e:
        print(e)
        if open_in_browser:
            webbrowser.open(iiwy_obj.url)
            webbrowser.open('http://already_submitted_error')
        return
    sub.set_flair(submission, flair_text='NEW IIWY', flair_css_class='images')
    submission.approve()
    print("NEW IIWY!!! WOOOOO!!!!")
    print(iiwy_obj.title)
    while True:
        try:
            comment_text = get_comment_text(iiwy_obj)
            comment = submission.add_comment(comment_text)
            comment.approve()
            break
        except requests.exceptions.HTTPerror:
            pass

    # old rewatch/discussion
    bottom_sticky = sub.get_sticky(bottom=True)
    bottom_sticky.unsticky()
    # old IIWY
    top_sticky = sub.get_sticky(bottom=False)
    top_sticky.unsticky()

    # new IIWY
    try:
        submission.sticky(bottom=False)
    except Exception as e:
        print("Caught exception while trying to sticky:", e)
    # old rewatch/discussion
    try:
        bottom_sticky.sticky(bottom=True)
    except Exception as e:
        print("Caught exception while trying to sticky:", e)

    submission.distinguish()
    if open_in_browser:
        webbrowser.open(submission.permalink)
    iiwy_obj.reddit_url = submission.permalink
    past_history.add_iiwy(iiwy_obj)
    past_history.write()
    print("Successfully submitted link! Time to celebrate.")

# check for a new IIWY
def check_iiwy():
    global i, foundlist, debug, r, user, paw, subreddit
    iiwy_obj = iiwy.get_iiwy_info()
    if iiwy_obj.number in foundlist or iiwy_obj.duration in foundlist: # if episode found before
        printinfo(i)
        i += 1
        return
    if not debug:
        while True:
            try:
                post_iiwy(iiwy_obj)
            except requests.exceptions.HTTPError:
                print("HTTP error while trying to submit - retrying to resubmit")
                pass
            except praw.errors.AlreadySubmitted:
                print('Already submitted.')
                break
            except Exception as e:
                print("Error", e)
                break
    foundlist.append(iiwy_obj.duration)
    foundlist.append(iiwy_obj.number)
    printinfo(i)
    i += 1


discussion_string = '''\
Montly discussion posts will be posted on the last weekend of every month, and subreddit rewatch episodes will be posted on the other days!

Suggested topics:

* Favorite: episode, quote, or podcast.  
* Least favorite: episode, quote, or podcast.  
* What did you think of the latest episode or podcast?  
* Any ideas or suggestions for the subreddit?  
* General observations or musings.

These are just suggestions, so feel free to talk about anything that you want and discuss with others!
'''

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

# returns true on the last weekend of the month
def time_to_post_discussion(dt):
    day_of_month = int(dt.strftime('%d'))
    month, year = int(dt.strftime('%m')), int(dt.strftime('%Y'))
    num_days_in_mo = calendar.monthrange(year, month)[1]
    if day_of_month >= num_days_in_mo - 7 and day_of_month != num_days_in_mo:
        return True
    else:
        return False

# list of emails to notify for the subreddit discussion
def send_emails(permalink):
    try:
        global next_episode
        email_list = []
        params = {
                'api_user': reddit_password.get_sendgrid_username(),
                'api_key': reddit_password.get_sendgrid_password(),
                'to[]':'cmey63@gmail.com',
                'bcc[]':email_list,
                'subject':'Jake and Amir Subreddit Rewatch #%d' %(next_episode),
                'text': permalink,
                'from':'ericbailey94' + '@' + 'gmail.com', #for antispam
        }
        url = 'https://api.sendgrid.com/api/mail.send.json'
        r = requests.post(url, params=params)
        print(r.text)
    except Exception as e:
        print(e)

first_day = True

# If it just turned the last weekend of the month EST, post the monthly discussion.
# else, post the next subreddit rewatch (pointed to by next_episode) and sticky it.
def mod_actions():
    global next_episode, debug, r, user, paw, day, discussion_string
    global first_day
    episode = episodes[next_episode-1]
    today_datetime = datetime.datetime.now()
    new_day = today_datetime.strftime('%A')
    if new_day != day: # on a new day at midnight
        day = new_day
        first_day = False
        if new_day in ['Saturday', 'Sunday'] and time_to_post_discussion(today_datetime): # post discussion of the month
            if new_day == 'Saturday': # don't post it twice (once on sunday and once on saturday - just once on the weekend)
                title = 'Monthly Jake and Amir Discussion (%s)' % today_datetime.strftime('%B %Y')
                submission = submit(title, text=discussion_string)
                if open_in_browser:
                    webbrowser.open(submission.permalink)
                submission.sticky(bottom=True)
                submission.distinguish()
                sub.set_flair(submission, flair_text='DISCUSSION POST', flair_css_class='video')
                print("Successfully submitted sticky! Time to celebrate.")
        # post rewatch episode (every day other than discussion days)
        elif not first_day and new_day in ['Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']: 
        #elif new_day in []:
            episode = episodes[next_episode-1] # next_episode is indexed by 1
            if ',,' in episode.title: # multipart episode
                episode_title = episode.title.split(',,')[0].split('Part')[0].split('Pt.')[0].split('pt.')[0].split('Ep.')[0].strip()
                title = 'Subreddit Rewatch #%d: %s (Series) (%s - %s)' %(next_episode, episode_title, episode.date_str.split(',,')[0], episode.date_str.split(',,')[-1])
                submission = submit(title, text=get_multipart_string(episode))
            else:
                title = 'Subreddit Rewatch #%d: %s (%s)' %(next_episode, episode.title, episode.date_str)
                submission = submit(title, text=get_rewatch_string(episode))
            if open_in_browser:
                webbrowser.open(submission.permalink)
            submission.sticky(bottom=True)
            submission.distinguish()
            sub.set_flair(submission, flair_text='REWATCH', flair_css_class='modpost')
            send_emails(submission.permalink)
            print("Successfully submitted sticky! Time to celebrate.")
            next_episode += 1

def adjust_timeout():
    global timeout
    hour = int(datetime.datetime.now().strftime('%H'))
    day = datetime.datetime.now().strftime('%A')
    if (hour, day) in [
            (23, 'Sunday'), (0, 'Monday'), (1, 'Monday'), (2, 'Monday'), # IIWY episodes
            (23, 'Wednesday'), (0, 'Thursday'), (1, 'Thursday'), (2, 'Thursday') # IIWY bonus episodes
        ]:
        timeout = 1
    else:
        timeout = default_timeout

############################ LOGIC #############################

day = datetime.datetime.now().strftime('%A')

iiwy_obj = iiwy.get_iiwy_info()
print("Name of most recent IIWY is: \"" + iiwy_obj.title + "\"", "with URL", iiwy_obj.url,
      "and description", iiwy_obj.desc, "and sponsors", iiwy_obj.sponsor_list,
      "and duration", iiwy_obj.duration)

def printinfo(i):
    global next_episode
    print(i, end=' ')
    if i % 25 == 13:
        print('- previous episode: #%d (%s)' % (next_episode-1, episodes[next_episode-2].title), end=' ')
    if i % 25 == 14:
        print('- next episode: #%d (%s)' % (next_episode, episodes[next_episode-1].title), end=' ')
    if debug:
        print(foundlist if i % 5 == 1 else "")
    else:
        print(foundlist if i % 25 == 1 else "")

i = 1

foundlist = [DEFAULT_STR]
foundlist.append(iiwy_obj.number)
foundlist.append(iiwy_obj.duration)

while True:
    check_iiwy()

    if next_episode > -1:
        mod_actions()

    adjust_timeout()

    if timeout != 0:
        time.sleep(timeout)

