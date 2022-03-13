from operator import truediv
import tkinter as tk
import datetime
import keyboard
from win10toast import ToastNotifier
import pandas as pd
from hanging_threads import start_monitoring
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer
import openpyxl

start_monitoring(seconds_frozen=10, test_interval=100)

"""
function to get the focused window title for autologging
https://stackoverflow.com/questions/10266281/obtain-active-window-using-python
"""
def getForegroundWindowTitle() -> Optional[str]:
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)
    
    # 1-liner alternative: return buf.value if buf.value else None
    if buf.value:
        return buf.value
    else:
        return None


"""
VARIABLES INIT
""" 
running = False
autoactive = False
start_time= 0
activity_start= None
active=False
activity_time= 0
listactivities=[]
listtimes=[]
activity_text="None"

"""
GUI INIT
"""

# ***** WIDGETS *****
# create main window
root = tk.Tk()
root.geometry('485x320')
root.title('Moktime')
activity=tk.StringVar()
activity.set("Current Activity: "+activity_text)
autologger=tk.StringVar()
autologger.set("Enable Autologger")

"""
NOTIFICATIONS
"""
def notify(msg):
    toaster = ToastNotifier()
    toaster.show_toast("Moktime", str(msg), icon_path='timer/mug.ico', duration=2, threaded=True)


"""
STOPWATCH
"""
#functions
def start():
    global running
    print("start")
    global start_time
    global activity_start
    if start_time==0: #new stopwatch
        start_time=datetime.datetime.now()
    else: #take into account paused time
        global pause_time
        print(start_time)
        difference_time = (datetime.datetime.now()-pause_time)
        print(difference_time)
        start_time = start_time + difference_time
        if active:
            activity_start = activity_start + difference_time
        print(start_time)
    if not running:
        print("calling update")
        update()
        print("update called")
        running = True

def pause():
    global running
    if running: #pause and register when to compensate later
        stopwatch_label.after_cancel(update_time)
        global pause_time
        pause_time = datetime.datetime.now()
        running = False

def switch():
    global running
    if running:
        pause()
        notify("Timer paused.")
    else:
        start()
        notify("Timer started.")

def reset(): #set everything to zero
    global running
    print("reset")
    if running:
        stopwatch_label.after_cancel(update_time)
        running = False
    global total_time 
    total_time = 0
    global start_time
    start_time = 0
    #stopwatch_label.config(text='0:00:00') not needed?

def update(): #calculate time by difference between now and the start, round to seconds
    global total_time
    global activity_time
    global activity_start
    global autoactive
    print("update")
    total_time = datetime.datetime.now()-start_time
    if active:
        print("update activitytime")
        activity_time= roundTime(datetime.datetime.now()-activity_start)
        print("activity time updated")
        if autoactive:
            currentfocus = getForegroundWindowTitle()
            listtimes[-1]=activity_time.total_seconds()
            print(currentfocus)
            if listactivities[-1]!=currentfocus:
                activity_start=datetime.datetime.now()                               
                listactivities.append(currentfocus)
                listtimes.append(roundTime(datetime.datetime.now()-activity_start).total_seconds())



    stopwatch_label.config(text=str(roundTime(total_time)))  
    print(total_time)
    global update_time
    update_time = stopwatch_label.after(1000, update)

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

def autoActivity():
    global autoactive
    global active
    global activity_start
    global listactivities

    if not autoactive:
        autoactive = True
        autologger.set("Disable Autologger")
        pause()
        active = True
        activity_start = datetime.datetime.now()
        if not listactivities:
            listactivities.append(getForegroundWindowTitle())
        if not listtimes:
            listtimes.append(roundTime(datetime.datetime.now()-activity_start).total_seconds())
        activity.set("Logging active window")
        notify("Autologging started, timer started.")
        start()
    else:
        autoactive = False
        autologger.set("Enable Autologger")
        active = False
        activity.set("None")
        notify("Autologging stopped, timer paused.")
        pause()


   
def startActivity():
    global listactivities
    global activity_time
    global activity_start
    global active
    global activity
    global autoactive
    global activity_text

    autoactive = False
    pause()
    active = True
    activity_text=activity_entry.get()
    activity.set("Current Activity: "+activity_text)
    activity_start = datetime.datetime.now()
    listactivities.append(activity_text)
    notify("Activity "+activity_text+" started!")
    print(listactivities)
    print("trying to start")
    start()

def logActivity():
    global listtimes
    global activity_time
    global active
    if not activity_time==0:
        pause()
        if len(listactivities) != len(listtimes):
            listtimes.append(activity_time.total_seconds())
        else:
            listtimes[-1]=activity_time.total_seconds()
        notify("Logged activity "+activity_text+" for "+str(listtimes[-1]))
        start()
        print(listtimes)

def saveQuit():
    global df
    global listtimes
    global listactivities
    df = pd.DataFrame(list(zip(listactivities, listtimes)),
               columns =['Activity / Window', 'Time (s)'])
    df.to_excel("output.xlsx")  
    root.destroy()

"""
BUILD GUI
"""

# label to display time
stopwatch_label = tk.Label(root, text='0:00:00', font=('Arial', 30))
stopwatch_label.pack(fill='x')

#activity display and logging


activity_label = tk.Label(root, textvariable=activity, font=('Arial', 14))
activity_label.pack(fill='x')
activity_entry = tk.Entry(root)
activity_entry.pack(fill='x')
activity_button = tk.Button(text='Start new activity', height=2, width=7, font=('Arial', 12), command=startActivity)
activity_button.pack(fill='x')
log_button = tk.Button(text='Log activitytime', height=2, width=7, font=('Arial', 12), command=logActivity)
log_button.pack(fill='x')
log_button = tk.Button(textvariable=autologger, height=2, width=7, font=('Arial', 12), command=autoActivity)
log_button.pack(fill='x')
# start, pause, reset, quit buttons
start_button = tk.Button(text='start', height=1, width=7, font=('Arial', 12), command=start)
start_button.pack(expand=True, fill='both', side='left')
pause_button = tk.Button(text='pause', height=1, width=7, font=('Arial', 12), command=pause)
pause_button.pack(expand=True, fill='both', side='left')
reset_button = tk.Button(text='reset', height=1, width=7, font=('Arial', 12), command=reset)
reset_button.pack(expand=True, fill='both', side='left')
quit_button = tk.Button(text='save & quit', height=1, width=7, font=('Arial', 12), command=saveQuit)
quit_button.pack(expand=True, fill='both', side='left')

"""
GLOBAL HOTKEYS
"""
keyboard.add_hotkey('ctrl+space', switch)

"""
MAIN LOOP
"""
root.mainloop()

