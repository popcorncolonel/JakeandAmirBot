import re
import sys
import time
import urllib2
import requests
import datetime
import calendar
import warnings
import webbrowser
import HTMLParser
from rewatch import episodes
from BeautifulSoup import BeautifulSoup
# have to create a reddit_password.py file with a get_password() function
import reddit_password

open_in_browser = False

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import praw

SENTINEL = ''
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
    print 'Previous episode:', episodes[next_episode-2]
    print 'Next episode to be posted:', episodes[next_episode-1]
    time.sleep(3)

timeout = default_timeout = 5 #don't spam the servers :D

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
 
# returns a tuple (string, string) representing the title and URL
#    of the most recent If I Were You episode
def get_iiwy_info(depth=0):
    (name, url, desc, sponsorlist) = (SENTINEL, SENTINEL, SENTINEL, [])
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = requests.get('https://www.spreaker.com/user/ifiwereyou', timeout=10)
        soup = BeautifulSoup(''.join(r.text))
        episode_part = soup.findAll('h2', {'class':'track_title'})[0]
        #episode_part = episode_part.contents[3]
        episode_part = episode_part.findAll('a')[0]
        name = episode_part.text
        url = episode_part['href']
        duration = soup.findAll('div', {'class':'trkl_ep_duration'})[0].contents[0].strip()
        if len(duration) > 0:
            minutes = int(duration.split(':')[0])
            if minutes >= 60:
                hours = str(minutes / 60)
                minutes = '%02d' % (minutes % 60)
                duration = hours + ':' + minutes + ':' + duration.split(':')[1]
            name += ' [' + duration + ']'
        def get_sponsors(sponsors):
            sponsorlist = []
            if ',' in sponsors: # Squarespace.com, MeUndies.com, and DollarShaveClub.com!
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
            elif ' and ' in sponsors: # Squarespace.com and DollarShaveClub.com
                sponsorlist.append(sponsors.split(' and ')[0].strip())
                sponsorlist.append(sponsors.split(' and ')[1].strip().rstrip('.').rstrip('!'))
            else: # MeUndies.com
                sponsorlist.append(sponsors.strip().rstrip('.').rstrip('!'))
            return sponsorlist
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = requests.get(url, timeout=10)
            soup = BeautifulSoup(''.join(r.text))
            desc = soup.findAll('div', {'class':'track_description'})[0].contents
            desctext = desc[0].strip()
            longtext = ''.join([str(s) for s in desc])
            desc = desctext
            sponsors = longtext.split('brought to you by ')[1].strip()
            sponsorlist = get_sponsors(sponsors)
        except IndexError:
            desc = SENTINEL
            sponsorlist = []
    except (KeyboardInterrupt, SystemExit):
        raise
    except requests.exceptions.Timeout:
        print "encountered spreaker Timeout. recursing."
        time.sleep(3)
        return get_iiwy_info()
    except Exception as e:
        print "encountered spreaker error =("
        print e
        time.sleep(3)
        return get_iiwy_info(depth=depth+1)
    try:
        if 'If I Were You' not in name:
            name = "If I Were You " + name
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print "encountered iiwy error :(((("
        print e
        time.sleep(3)

    def to_reddit_url(link):
        if '.com' in link or '.org' in link or '.net' in link:
            link = '['+link.split('.com')[0].split('.org')[0].split('.net')[0]+'](http://'+link.lower()+')'
        return link

    sponsorlist = map(to_reddit_url, sponsorlist)
    desc = desc.replace('"', "'").strip()
    return (name, url, desc, sponsorlist, duration)

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
            print "had trouble submitting D: HTTPError."
            print e
            time.sleep(3)
            pass
        except Exception as e:
            print "had trouble submitting D:"
            print e
            time.sleep(3)
            break


# check for a new IIWY
def check_iiwy():
    global iiwyname, iiwyurl, desc, sponsor_list, duration, foundlist, i, debug, r, user, paw, subreddit
    (iiwyname, iiwyurl, desc, sponsor_list, duration) = get_iiwy_info()
    if duration in foundlist and 'Episode ' not in iiwyname: # spreaker error
        pass
    elif iiwyname in foundlist: # if episode found before
        pass
    else: # if new episode
        if not debug:
            while True:
                try:
                    if open_in_browser:
                        webbrowser.open(iiwyurl)
                    r.login(user, paw)
                    try:
                        submission = r.submit(subreddit, iiwyname, url=iiwyurl)
                    except praw.errors.AlreadySubmitted as e:
                        print e
                        if open_in_browser:
                            webbrowser.open(iiwyurl)
                            webbrowser.open('http://already_submitted_error')
                        break
                    sub.set_flair(submission, flair_text='NEW IIWY', flair_css_class='images')
                    submission.approve()
                    print "NEW IIWY!!! WOOOOO!!!!"
                    print iiwyname
                    while True:
                        try:
                            comment = ''
                            comment += '"'+desc+'"\n\n---\n\n###Links\n\n [TextJake.com](http://textjake.com/)\n\n [If I Were You Bingo](http://iiwybingo.appspot.com)\n\n [Source Code](https://github.com/popcorncolonel/JakeandAmirBot)'
                            if sponsor_list != []:
                                n_sponsors = len(sponsor_list)
                                last_sponsor = sponsor_list[-1]
                                comment += '\n\n This episode\'s sponsors: '
                                if n_sponsors == 1:
                                    comment += sponsor_list[0]
                                elif n_sponsors == 2:
                                    comment += sponsor_list[0] + ' and ' + sponsor_list[1]
                                elif n_sponsors == 3:
                                    comment += (sponsor_list[0] + ', ' +
                                                sponsor_list[1] + ', and ' + 
                                                sponsor_list[2])
                                elif n_sponsors == 4:
                                    comment += (sponsor_list[0] + ', ' +
                                                sponsor_list[1] + ', ' +
                                                sponsor_list[2] + ', and ' + 
                                                sponsor_list[3])
                            comment = submission.add_comment(comment)
                            comment.approve()
                            break
                        except requests.exceptions.HTTPerror:
                            pass

                    # old rewatch/discussion
                    bottom_sticky = sub.get_sticky()
                    bottom_sticky.unsticky()
                    # old IIWY
                    top_sticky = sub.get_sticky()
                    top_sticky.unsticky()

                    # new IIWY
                    submission.sticky(bottom=False)
                    # old rewatch/discussion
                    bottom_sticky.sticky(bottom=True)

                    submission.distinguish()
                    if open_in_browser:
                        webbrowser.open(submission.permalink)
                    print "Successfully submitted link! Time to celebrate."
                    break
                except requests.exceptions.HTTPError:
                    pass
                except praw.errors.AlreadySubmitted:
                    print 'already submitted.'
                    break
                except:
                    break
        foundlist.append(duration)
        foundlist.append(iiwyname)
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
        print r.text
    except Exception as e:
        print e

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
                print "Successfully submitted sticky! Time to celebrate."
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
            print "Successfully submitted sticky! Time to celebrate."
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

(iiwyname, iiwyurl, desc, sponsor_list, duration) = get_iiwy_info()
print "Name of most recent IIWY is: \"" + iiwyname + "\"", "with URL", iiwyurl, "and description", desc, "and sponsors", sponsor_list, "and duration", duration

def printinfo(i):
    global next_episode
    print i,
    if i % 25 == 13:
        print '- previous episode: #%d (%s)' % (next_episode-1, episodes[next_episode-2].title),
    if i % 25 == 14:
        print '- next episode: #%d (%s)' % (next_episode, episodes[next_episode-1].title),
    if debug:
        print foundlist if i % 5 == 1 else ""
    else:
        print foundlist if i % 25 == 1 else ""

i = 1

foundlist = [SENTINEL]
foundlist.append(iiwyname)
foundlist.append(duration)

while True:
    check_iiwy()

    if next_episode > -1:
        mod_actions()

    adjust_timeout()

    if timeout != 0:
        time.sleep(timeout)

