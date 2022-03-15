from operator import truediv
from socket import timeout
import tkinter as tk
import datetime
import keyboard
from win10toast import ToastNotifier
import pandas as pd
from hanging_threads import start_monitoring
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer
import win32gui, win32api, win32process, psutil, threading


def getForegroundWindowTitle() -> Optional[str]:
    """
    function to get the focused window title for autologging
    from: https://stackoverflow.com/questions/10266281/obtain-active-window-using-python
    """
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)
    
    # 1-liner alternative: return buf.value if buf.value else None
    if buf.value:
        return buf.value
    else:
        return None

def getIdleTime():
    """
    function the get current windows user idle time 
    from: https://stackoverflow.com/questions/911856/detecting-idle-time-using-python
    """
    return (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0


def active_window_process_name():
    """
    function to get process name of active window
    from: https://stackoverflow.com/questions/14394513/win32gui-get-the-current-active-application-name
    """
    try:
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow()) #This produces a list of PIDs active window relates to
        return psutil.Process(pid[-1]).name() #pid[-1] is the most likely to survive last longer
    except:
        pass

def roundTime(dt=None, date_delta=datetime.timedelta(seconds=1), to='average'):
    """
    Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    from:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
    """
    round_to = date_delta.total_seconds()
    if dt is None:
        dt = datetime.now()
    seconds = (dt - dt.min).seconds

    if seconds % round_to == 0 and dt.microseconds == 0:
        rounding = (seconds + round_to / 2) // round_to * round_to
    else:
        if to == 'up':
            # // is a floor division, not a comment on following line (like in javascript):
            rounding = (seconds + dt.microseconds/1000000 + round_to) // round_to * round_to
        elif to == 'down':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to

    return dt + datetime.timedelta(0, rounding - seconds, - dt.microseconds)


def notify(msg):
    """
    makes a win10 notification in a new thread.
    """
    toaster = ToastNotifier()
    toaster.show_toast("Moktime", str(msg), icon_path='timer/mug.ico', duration=2, threaded=True)

