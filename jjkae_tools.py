from __future__ import print_function

def printinfo(i, episodes, foundlist, debug, next_episode):
    print(i, end=' ')
    if next_episode > -1:
        if i % 25 == 13:
            print('- previous episode: #%d (%s)' % (next_episode-1, episodes[next_episode-2].title), end=' ')
            if i % 25 == 14:
                print('- next episode: #%d (%s)' % (next_episode, episodes[next_episode-1].title), end=' ')
            else:
                if i % 25 == 13:
                    print(foundlist, end=' ')
                if debug:
                    print(foundlist if i % 5 == 1 else "")
                else:
                    print(foundlist if i % 25 == 1 else "")

