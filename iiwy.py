import sys
import time
import history
import requests
import warnings

python_3 = False
if sys.version_info >= (3, 0):
    python_3 = True
    from bs4 import BeautifulSoup
else:
    from BeautifulSoup import BeautifulSoup

DEFAULT_STR = ''

class IIWY:
    def __init__(self, number, title, duration, monthstring, sponsor_list, url=None, reddit_url=None, desc=None):
        self.number = number
        self.title = title
        self.duration = duration
        self.monthstring = monthstring
        self.sponsor_list = sponsor_list
        self.reddit_url = reddit_url
        self.url = url
        self.desc = desc

    def __repr__(self):
        return "IIWY submission object: " + self.title

    def __str__(self):
        return self.__repr__()

# returns a tuple (string, string) representing the title and URL
#    of the most recent If I Were You episode
def get_iiwy_info(depth=0):
    (name, url, desc, sponsorlist) = (DEFAULT_STR, DEFAULT_STR, DEFAULT_STR, [])
    try:
        r = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = requests.get('https://www.spreaker.com/user/ifiwereyou', timeout=10)
        if python_3:
            soup = BeautifulSoup(''.join(r.text), "html.parser")
        else:
            soup = BeautifulSoup(''.join(r.text))
        episode_part = soup.findAll('h2', {'class':'track_title'})[0]
        episode_part = episode_part.findAll('a')[0]
        name = episode_part.text
        url = episode_part['href']
        duration = soup.findAll('div', {'class':'trkl_ep_duration'})[0].contents[0].strip()
        if len(duration) > 0:
            minutes = int(duration.split(':')[0])
            if minutes >= 60:
                hours = str(minutes // 60)
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
            if python_3:
                soup = BeautifulSoup(''.join(r.text), "html.parser")
            else:
                soup = BeautifulSoup(''.join(r.text))
            desc = soup.findAll('div', {'class':'track_description'})[0].contents
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
        return get_iiwy_info(depth=depth+1)
    episode_num = name.split(':')[0].split('Episode ')[1]
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

    def to_reddit_url(link):
        if '.com' in link or '.org' in link or '.net' in link:
            link = '['+link.split('.com')[0].split('.org')[0].split('.net')[0]+'](http://'+link.lower()+')'
        return link

    sponsorlist = list(map(to_reddit_url, sponsorlist))
    desc = desc.replace('"', "'").strip()
    iiwy_obj = IIWY(number=episode_num, title=name, duration=duration,
                    monthstring=history.this_monthstring(), url=url,
                    sponsor_list=sponsorlist, desc=desc)
    return iiwy_obj

if __name__ == '__main__':
    print(get_iiwy_info())

