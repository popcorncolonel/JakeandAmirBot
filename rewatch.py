with open('episodes.txt', 'r') as f:
    episodes = list(f)[1:]
episodes = [x.split('|')[1:-1] for x in episodes]

class Episode(object):
    def __init__(self, date_str, title, url, duration, bonus_footage):
        self.date_str = date_str
        self.title = title
        self.url = url
        self.duration = duration
        self.bonus_footage = bonus_footage
    
    def __str__(self):
        return self.title + ' - ' + self.date_str

    def __repr__(self):
        return self.__str__()

#converts from list form to object form
def transform(episode):
    return Episode(episode[0], episode[1], episode[2], episode[4], episode[5] or None)

episodes = [transform(episode) for episode in episodes]

#https://gdata.youtube.com/feeds/api/videos?q=jake+and+amir+notified&max-results=2&v=2&alt=json
if __name__ == '__main__':
    for episode in episodes:
        print(episode)
        print()
        if 'jakeandamir' in episode.url:
            print(episode)
