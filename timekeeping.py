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
import os

#generalfunctions.py contains functions that aren't specific to this project
from generalfunctions import *

#enable for debugging hanging thread
#start_monitoring(seconds_frozen=10, test_interval=100)

"""
OLD VERSION
DISREGARD
RUN MOKTIME.PY INSTEAD
"""



"""
VARIABLES INIT
""" 
running = False
autoactive = False
start_time= 0
activity_start= datetime.datetime.now()
activity_time= 0
listactivities=[]
listtimes=[]
activity_text=""
listprocess=[]
liststart=[]
listpause=[]
listplan=[]
pause_time=0
notifiedidle=True
timeout = 60 #standard timeout time in seconds

"""
GUI INIT
"""

# ***** WIDGETS *****
# create main window
root = tk.Tk()
root.geometry('400x300')
root.title('Moktime')
activity=tk.StringVar()
activity.set(activity_text)
autologger=tk.StringVar()
autologger.set("Enable Autologger")
startvar=tk.StringVar()
startvar.set("Start new timer")
timeoutvar=tk.IntVar()
timeoutvar.set(timeout)


"""
MAIN PROGRAM 
"""

def start():
    """
    Starts the timer. If previously paused log the paused time.
    """
    global running
    global start_time
    global activity_start
    global pause_time

    if start_time==0: #new stopwatch
        start_time=datetime.datetime.now()
    else: #take into account paused time
        global pause_time
        difference_time = roundTime((datetime.datetime.now()-pause_time))
        listpause[-1] = difference_time
        start_time = start_time + difference_time
        activity_start = activity_start + difference_time
    if not running:
        startvar.set("Pause timer")
        update()
        running = True

def pause(msg=""):
    """
    Stop updating and mark the time when paused.
    Optional: give string for notification.
    """
    global pause_time
    global running
    if running: #pause and register when to compensate later
        startvar.set("Resume timer")
        stopwatch_label.after_cancel(update_time)
        global pause_time
        pause_time = datetime.datetime.now()
        running = False
    
    if not (msg==""):
        notify(msg)

def switch():
    """
    Switch between running and stopped.
    """
    global running
    if running:
        startvar.set("Resume timer")
        pause("Timer paused.")
    else:
        startvar.set("Pause timer")
        start()
        notify("Timer started.")

def reset(): 
    """
    Reset the global time and current activity starttime to zero.
    """
    global running
    if running:
        pause()
    global total_time 
    global start_time
    global activity_start

    if not autoactive:
        logActivity()
    else:
        autoActivity()

    startvar.set("Start new timer")
    activity_start= datetime.datetime.now()
    total_time = 0
    start_time = 0
    stopwatch_label.config(text='00:00:00')

def update(): 
    
    """
    Do stuff while running: calculate elapsed time total and per activity
    if autologging: handle getting current process info and log it as well
    Also auto-pauses when no input is detected for a minute
    TODO: move all list manipulations to central function
    """
    global total_time
    global activity_time
    global activity_start
    global autoactive
    global notifiedidle
    
    total_time = datetime.datetime.now()-start_time
    timeout=int(timeout_entry.get())
    activity_time= roundTime(datetime.datetime.now()-activity_start)
    if autoactive:
        currentfocus = getForegroundWindowTitle()
        currentprocess = active_window_process_name()
        listtimes[-1]=activity_time.total_seconds()
        if listactivities[-1]!=currentfocus:
            activity_start=datetime.datetime.now()
            liststart.append(activity_start)                               
            listactivities.append(currentfocus)
            listprocess.append(currentprocess)
            listtimes.append(roundTime(datetime.datetime.now()-activity_start).total_seconds())
            listpause.append(0)
            listplan.append(activity_text)

    stopwatch_label.config(text=str(roundTime(total_time)))  
    global update_time
    update_time = stopwatch_label.after(1000, update)

    idletime=getIdleTime()
    if idletime>timeout and notifiedidle:
        notify("You've been idle for "+str(timeout)+" seconds. Logging will autopause in 5 seconds if no further input is detected.")
        notifiedidle=False
    if idletime<timeout and not notifiedidle:
        notifiedidle=True
    if idletime>timeout+5:
        notifiedidle=True
        pause("Autopausing logging after "+str(timeout+5)+" seconds of detected idletime.")



def autoActivity():
    """
    Enable autologging of current proces and time spent.
    Switchable function, if called it switches between autlogging/stop autologging.
    TODO: move all list manipulations to central function
    """
    global autoactive
    global activity_start
    global listactivities
    global listprocess
    global activity_text

    if not autoactive:
        autoactive = True
        autologger.set("Disable Autologger")
        pause()
        activity_start = datetime.datetime.now()
        if not listactivities:
            listactivities.append(getForegroundWindowTitle())
            listprocess.append(active_window_process_name())
            listplan.append(activity_text)
            liststart.append(activity_start)
            listpause.append(0)
        if not listtimes:
            listtimes.append(roundTime(datetime.datetime.now()-activity_start).total_seconds())
        activity.set("Logging active window")
        notify("Autologging started, timer started.")
        log_button.config(state="disabled")
        start()
    else:
        autoactive = False
        autologger.set("Enable Autologger")
        log_button.config(state="normal")
        pause("Autologging stopped, timer paused.")


   
def startActivity():
    """
    Add an activity title.
    TODO: move all list manipulations to central function
    """
    global listactivities
    global activity_time
    global activity_start
    global activity
    global autoactive
    global activity_text

    pause()
    activity_text=activity_entry.get()
    activity.set(activity_text)
    activity_start = datetime.datetime.now()
    listactivities.append("")
    liststart.append(activity_start)
    listprocess.append("Manual Log")
    listpause.append(0)
    listplan.append(activity_text)
    notify("Activity "+activity_text+" started!")
    start()

def logActivity():
    """
    Update time on current activity. 
    TODO: move all list manipulations to central function
    """
    global listtimes
    global activity_time
    if not activity_time==0:
        pause()
        if len(listactivities) != len(listtimes):
            listtimes.append(activity_time.total_seconds())
        else:
            listtimes[-1]=activity_time.total_seconds()
        notify("Logged activity "+activity_text+" for "+str(listtimes[-1]))
        start()

def updateLists():
    """
    Depending on state: update all logging lists.
    TODO: make this thing and replace
    """


def saveQuit():
    """
    Finish up logging the activity and pause time if needed.
    Zip data into dataframe and save to file.
    Stop the program.
    """
    global df
    global listtimes
    global listactivities

    if not autoactive:
        logActivity()
    if not running and pause_time>0:
        difference_time = roundTime((datetime.datetime.now()-pause_time))
        listpause[-1] = difference_time
    
    df = pd.DataFrame(list(zip(listplan, listactivities, listprocess, liststart, listtimes, listpause )),
               columns =['Activity', 'Window', 'Software', 'Start time', 'Time spent (s)', 'Time paused (s)'])
    
    output_path="output.csv"
    try:
        df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
    except PermissionError:
        timestring = datetime.datetime.now().strftime("%m%d%Y%H%M%S")
        print("Cannot save, output.csv is currently in use. Using alternative name output"+timestring+".csv")
        df.to_csv(output_path+timestring, mode='a', header=not os.path.exists(output_path+timestring),index=False)  
    
    root.destroy()
  


"""
BUILD GUI
TODO: fix layout
"""




# label to display time
stopwatch_label = tk.Label(root, text='00:00:00', font=('Arial', 50))
#stopwatch_label.pack(fill='x')
stopwatch_label.grid(column=0,row=0,columnspan=2)
#activity display and logging


#activity_label = tk.Label(root, textvariable=activity, font=('Arial', 14))
#activity_label.pack(fill='x')
#activity_label.grid(column=0,row=1,columnspan=3)

activity_label = tk.Label(text="Current Activity: ")
activity_label.grid(column=0, row=1)

activity_entry = tk.Entry(root, textvariable=activity)
#activity_entry.pack(fill='x')
activity_entry.grid(column=1,row=1)

activity_button = tk.Button(text='Set title current plan', font=('Arial', 12), command=startActivity)
#activity_button.pack(fill='x')
activity_button.grid(column=2,row=1)

log_button = tk.Button(text='Log activity time', font=('Arial', 12), command=logActivity)
log_button.grid(column=0,row=2)
#log_button.pack(expand=True, fill='both',side='left')

timeout_label = tk.Label(text="Timeout period (s):")
timeout_label.grid(column=1, row=2)
timeout_entry = tk.Entry(root,textvariable=timeoutvar)
timeout_entry.grid(column=2,row=2)
#timeout_entry.pack(expand=True, fill='both',side='left')

autolog_button = tk.Button(textvariable=autologger, font=('Arial', 12), command=autoActivity)
#autolog_button.pack(fill='x')
log_button.grid(column=0,row=3, columnspan=2)

start_button = tk.Button(textvariable=startvar, font=('Arial', 12), command=switch)
start_button.grid(column=0,row=4)
#start_button.pack(expand=True, fill='both', side='left')

reset_button = tk.Button(text='reset',  font=('Arial', 12), command=reset)
reset_button.grid(column=1,row=4)
#reset_button.pack(expand=True, fill='both', side='left')

quit_button = tk.Button(text='save & quit',font=('Arial', 12), command=saveQuit)
quit_button.grid(column=2,row=4)
#quit_button.pack(expand=True, fill='both', side='left')

"""
GLOBAL HOTKEYS
"""
keyboard.add_hotkey('ctrl+space', switch)
keyboard.add_hotkey('shift+space', autoActivity)
"""
MAIN LOOP
"""
root.mainloop()

