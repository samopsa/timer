from operator import truediv
import tkinter as tk
import datetime
import keyboard
from win10toast import ToastNotifier
import pandas as pd

#init 
running = False
start_time=0
total_time=0
pause_time=0
activity_start=0
active=False
activity_time=0
activity="None"
listactivities=[]
listtimes=[]


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
        activity_start = activity_start + difference_time
        print(start_time)
    if not running:
        update()
        running = True

def pause():
    global running
    print("pause")
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
    stopwatch_label.config(text='0:00:00')

def update(): #calculate time by difference between now and the start, round to seconds
    global total_time
    global activity_time
    global activity_start
    print("update")
    total_time = datetime.datetime.now()-start_time
    activity_time= datetime.datetime.now()-activity_start
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
   
def startActivity():
    global listactivities
    global activity_time
    global activity_start
    global active
    global activity
    global display_var

    active = False
    activity = str(activity_entry.get())
    activity_start = datetime.datetime.now()
    activity_time=0
    listactivities.append(activity)
    print(listactivities)

def logActivity():
    global listtimes
    global activity_time
    global active
    if not activity_time==0:
        if not active:
            active=True
            listtimes.append(activity_time)
            activity_time=0
            print(listtimes)
        else:
            listtimes[-1]+=activity_time
            activity_time=0
            print(listtimes)





"""
GUI
"""

# ***** WIDGETS *****
# create main window
root = tk.Tk()
root.geometry('485x320')
root.title('Moktime')

# label to display time
stopwatch_label = tk.Label(root, text='0:00:00', font=('Arial', 80))
stopwatch_label.pack(fill='x')

#activity display and logging
activity_label = tk.Label(root, textvariable=activity, font=('Arial', 40))
activity_label.pack(fill='x')
activity_entry = tk.Entry(root)
activity_entry.pack(fill='x')
activity_button = tk.Button(text='Start activity', height=5, width=7, font=('Arial', 20), command=startActivity)
activity_button.pack(fill='x')
log_button = tk.Button(text='Log activity', height=5, width=7, font=('Arial', 20), command=logActivity)
log_button.pack(fill='x')
# start, pause, reset, quit buttons
start_button = tk.Button(text='start', height=5, width=7, font=('Arial', 20), command=start)
start_button.pack(expand=True, fill='both', side='left')
pause_button = tk.Button(text='pause', height=5, width=7, font=('Arial', 20), command=pause)
pause_button.pack(expand=True, fill='both', side='left')
reset_button = tk.Button(text='reset', height=5, width=7, font=('Arial', 20), command=reset)
reset_button.pack(expand=True, fill='both', side='left')
quit_button = tk.Button(text='quit', height=5, width=7, font=('Arial', 20), command=root.quit)
quit_button.pack(expand=True, fill='both', side='left')

"""
GLOBAL HOTKEYS
"""
keyboard.add_hotkey('ctrl+space', switch)

"""
NOTIFICATIONS
"""
def notify(msg):
    toaster = ToastNotifier()
    toaster.show_toast("Moktime", str(msg), icon_path=None, duration=1)

"""
MAIN LOOP
"""
root.mainloop()

