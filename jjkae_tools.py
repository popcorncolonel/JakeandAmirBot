from __future__ import print_function

import time
import requests
import datetime
import reddit_password


def printinfo(mod_info):
    print(mod_info.i, end=' ')
    if mod_info.next_episode > -1:
        if mod_info.i % 25 == 13:
            print('- previous episode: #%d (%s)' % (mod_info.next_episode-1, mod_info.episodes[mod_info.next_episode-2].title), end=' ')
        if mod_info.i % 25 == 14:
            print('- next episode: #%d (%s)' % (mod_info.next_episode, mod_info.episodes[mod_info.next_episode-1].title), end=' ')
    if mod_info.i % 25 == 1:
        print('- ', end='')
        print(mod_info.foundlist, end=' ')
    print()

def send_email(subject, body, to, bcc_list):
    try:
        params = {
                'api_user': reddit_password.get_sendgrid_username(),
                'api_key': reddit_password.get_sendgrid_password(),
                'to[]':to,
                'bcc[]':bcc_list,
                'subject': subject,
                'text': body,
                'from':'ericbailey94' + '@' + 'gmail.com', #for antispam
        }
        url = 'https://api.sendgrid.com/api/mail.send.json'
        r = requests.post(url, params=params)
        print(r.text)
    except Exception as e:
        print("TRIED TO SEND EMAIL. It didn't work.", e)

def send_rewatch_email(permalink, next_episode):
    """
    List of emails to notify for the subreddit discussion
    """
    email_list = []
    send_email(subject=u'Jake and Amir Subreddit Rewatch #{0}'.format(next_episode),
               body=permalink,
               to='cmey63@gmail.com',
               bcc_list=email_list)


def isnum(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def submit(title, mod_info, subreddit, text=None, url=None):
    """
    Submits the relevant information to the subreddit
    """
    while True:
        try:
            mod_info.login()
            if text:
                return mod_info.r.submit(subreddit, title, text=text, resubmit=True)
            elif url:
                return mod_info.r.submit(subreddit, title, url=url)
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

def get_day():
    today_datetime = datetime.datetime.now()
    day = today_datetime.strftime('%A')
    return day


def replace_top_sticky(sub, submission):
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