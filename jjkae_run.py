# https://stackoverflow.com/questions/44112399/automatically-restart-a-python-program-if-its-killed
import subprocess

filename = 'jjkae.py'
while True:
    """However, you should be careful with the '.wait()'"""
    p = subprocess.Popen('python3 '+filename, shell=True).wait()

    """#if your there is an error from running 'jjkae.py', 
    the while loop will be repeated, 
    otherwise the program will break from the loop"""
    if p != 0:
        continue
    else:
        break

