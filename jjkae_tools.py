from __future__ import print_function

import sys
import json
import time
import unittest
import requests
import datetime
import reddit_password

def is_python_3():
    return sys.version_info >= (3,0)

def printinfo(mod_info):
    print(mod_info.i, end=' ')
    if mod_info.i % 25 == 1:
        print('- ', end='')
        print(mod_info.foundlist, end=' ')
    print()

def send_email(subject, body, to, bcc_list=None):
    if bcc_list is None:
        bcc_list = []
    try:
        params = {
                'to[]':to, # this also works as a list :-) https://stackoverflow.com/questions/23384230/how-to-post-multiple-value-with-same-key-in-python-requests
                'bcc[]':bcc_list,
                'subject': subject,
                'text': body,
                'from':'ericbailey94' + '@' + 'gmail.com', #for antispam
        }
        headers = {'Authorization': "Bearer {}".format(reddit_password.get_sendgrid_api_key())}
        print(params)
        print(headers)
        url = 'https://api.sendgrid.com/api/mail.send.json'
        r = requests.post(url, params=params, headers=headers)
        print(r.text)
    except Exception as e:
        print("TRIED TO SEND EMAIL. It didn't work.", e)

def send_rewatch_email(permalink, title):
    """
    List of emails to notify for the subreddit rewatch
    """
    email_list = [
        'popcorncolonel' '@' 'gmail.com',
        'cmey63' '@' 'gmail.com',
        'gabedouda' '@' 'gmail.com',
    ]
    send_email(subject=u'Jake and Amir Subreddit Rewatch: {}'.format(title),
               body=permalink,
               to=email_list)


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
                return subreddit.submit(title, selftext=text, resubmit=True)
            elif url:
                return subreddit.submit(title, url=url)
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

def get_hour():
    today_datetime = datetime.datetime.now()
    hour = today_datetime.strftime('%H')
    return hour

def set_bottom_sticky(sub, submission):
    """
    try:
        top_sticky = sub.sticky(number=1)
        top_sticky.mod.sticky(state=False)
    except Exception as e:
        print("Caught exception while trying to unsticky:", e)
        send_email('J&ABot Error', e, 'popcorncolonel' '@' 'gmail.com')
    """
    submission.mod.sticky(bottom=True)
    submission.mod.distinguish()

def replace_top_sticky(sub, submission):
    # old rewatch
    bottom_sticky = sub.sticky(number=2)
    bottom_sticky.mod.sticky(state=False)
    # old IIWY
    top_sticky = sub.sticky(number=1)
    top_sticky.mod.sticky(state=False)

    # new IIWY
    try:
        submission.mod.sticky(bottom=False)
    except Exception as e:
        print("Caught exception while trying to sticky:", e)
        send_email('J&ABot Error', e, 'popcorncolonel' '@' 'gmail.com')
    # new GTD/Offdays
    try:
        bottom_sticky.mod.sticky(bottom=True)
    except Exception as e:
        print("Caught exception while trying to sticky:", e)
        send_email('J&ABot Error', e, 'popcorncolonel' '@' 'gmail.com')

    submission.mod.distinguish()

def start_test_thread(email_if_failures=False):
    # type: (bool) -> threading.Thread
    def run_tests():
        errors = run_jjkae_tests()
        if errors:
            error_synopsis = '\n\n'.join([str(error) for error in errors])
            error_synopsis.replace('\\n','\n').replace('\n', '\r\n')
            if email_if_failures:
                send_email('J&ABot Error', error_synopsis, 'popcorncolonel' '@' 'gmail.com')
            for error in errors:
                print(error)
            # sys.exit() #idk if I wanna sys.exit

    import threading
    t = threading.Thread(target=run_tests)
    t.daemon = True # makes calls to "sys.exit" actually exit the program within the thread
    t.start()
    return t

# Returns the list of errors of the tests
def run_jjkae_tests(verbosity=0):
    from tests import JjkaeTest
    suite = unittest.TestLoader().loadTestsFromTestCase(JjkaeTest)
    results = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return results.errors


def get_duration(video_id):
    url_fmtstring = 'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={key}&part=contentDetails&safeSearch=none'
    url = url_fmtstring.format(
        video_id=video_id,
        key=reddit_password.get_yt_api_key(),
    )
    resp = requests.get(
        url,
        timeout=15.,
        headers={
            'Cache-Control': 'max-age=0, no-cache',
        }
    )
    json_data = json.loads(resp.text)
    duration = None
    if 'items' in json_data and len(json_data['items']) > 0:
        content_details_duration = json_data['items'][0]['contentDetails']['duration']  # 'PT4M10S'
        minutes = int(content_details_duration[2:].split('M')[0])
        seconds = int(content_details_duration[-3:-1])
        duration = "{}:{}".format(minutes, seconds)
    return duration


if __name__ == '__main__':
    run_jjkae_tests()


