from __future__ import print_function

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


def send_emails(permalink):
    '''
    List of emails to notify for the subreddit discussion
    '''
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


def isnum(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
