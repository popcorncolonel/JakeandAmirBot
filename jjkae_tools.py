from __future__ import print_function

import time
import requests
import reddit_password


def printinfo(i, episodes, foundlist, next_episode):
    print(i, end=' ')
    if next_episode > -1:
        if i % 25 == 13:
            print('- previous episode: #%d (%s)' % (next_episode-1, episodes[next_episode-2].title), end=' ')
        if i % 25 == 14:
            print('- next episode: #%d (%s)' % (next_episode, episodes[next_episode-1].title), end=' ')
    if i % 25 == 1:
        print('- ', end='')
        print(foundlist, end=' ')
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

def submit(title, r, user, paw, subreddit, text=None, url=None):
    """
    Submits the relevant information to the subreddit
    """
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



