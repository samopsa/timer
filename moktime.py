from http.client import NOT_MODIFIED
from multiprocessing.dummy import current_process
from operator import truediv
from socket import timeout
from tkinter import *
from datetime import *
import keyboard
from win10toast import ToastNotifier
import pandas as pd
from hanging_threads import start_monitoring
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer
import win32gui, win32api, win32process, psutil, threading
import os
import humanize
from pathlib import Path
import operator
from pywinauto import Application

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("./assets")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

#generalfunctions.py contains functions that aren't specific to this project
from generalfunctions import *

#enable for debugging hanging thread
#start_monitoring(seconds_frozen=10, test_interval=100)

"""
INIT
""" 
root = Tk()

root.configure(bg = "#FFFFFF")

autologging = False

plan=StringVar()
plan.set("No plan set")
previoustask=plan.get()

running = False
timerstart= datetime.datetime.now()
pausetime=0
totaltime= datetime.timedelta(0)
totalpausetime=datetime.timedelta(0)
currenttasktime=datetime.timedelta(0)
currentURL=""
endTimeOutlookPlan=datetime.datetime(3500,1,1)

events=getCalendarEntries(3)
timezone = events['Start'][0].tzinfo


timeout = 120 #standard timeout for autopause in seconds
interval = 1000 #updateinterval in ms

listPlan = []
listWindow = []
listURL=[]
listProcess	= []
listStartTime = []
listDuration = []
listPause = []


app = Application(backend='uia')
app.connect(title_re=".*Chrome.*")
element_name="Address and search bar"
dlg = app.top_window()
url = dlg.child_window(title=element_name, control_type="Edit").get_value()


"""
MAIN PROGRAM
FUNCTIONS
"""


def update():
    """
    Main loop.
    Updates display
    Checks if logging is needed
    Checks if user is idle
    """
    global update_time
    global idletime
    global totaltime
    global totalpausetime
    global endTimeOutlookPlan

    now = datetime.datetime.now()

    if now > endTimeOutlookPlan: #call log if current outlooktask is finished
        endTimeOutlookPlan = datetime.datetime(3500,1,1)  #the future
        log()

    if running:
        #calculate time passed
        totaltime=(now-timerstart)

        #check for idle
        idletime = getIdleTime()
        if idletime > timeout:
            pause()

        #check if new log entry is needed. If only plan changes a manual is already trigged.
        #assumption: if process changes the windowtitle will always change as well so no need to check
        if (getForegroundWindowTitle() != listWindow[-1]) and (autologging):
            log()    

    
    else:
        #paused, so keep running tally of paused time
        totalpausetime=(now-pausetime)

    #update displays and loop  
    displayUpdate()
    update_time = root.after(interval, update)

def log():
    global currenttasktime
    global previoustask
    global endTimeOutlookPlan

    #check if there's a current outlook task, use that for plan
    now = datetime.datetime.now(timezone)
    for i in events['Start']:
        if i < now:
            if events['End'][events['Start'].index(i)] > now:
                plan.set(events['Subject'][events['Start'].index(i)])
                endTimeOutlookPlan=events['End'][events['Start'].index(i)]

    if len(listDuration): #calculate duration previous entry, obv. skip if there is no previous
        listDuration[-1]=roundTime(datetime.datetime.now()-listStartTime[-1])

    #log current states and reset times
    listPlan.append(plan.get())
    if len(listPlan) > 1 and listPlan[-1] != listPlan[-2]: #new plan? log previous one
        previoustask=listPlan[-2]
    
    if autologging:
        listWindow.append(getForegroundWindowTitle())
        listProcess.append(active_window_process_name())
        listURL.append(dlg.child_window(title=element_name, control_type="Edit").get_value())
    else:
        listWindow.append("Not logged")
        listProcess.append("Not logged")
        listURL.append("Not logged")
    

    listStartTime.append(datetime.datetime.now())
    listDuration.append(timedelta(0))
    listPause.append(timedelta(0))
    
    #calculate time spent on current task for display
    setlistplan=set(listPlan)
    if len(setlistplan)>1:
        startindex=len(listPlan) - operator.indexOf(reversed(listPlan), previoustask)
        currenttasktime = sum(listDuration[startindex:],datetime.timedelta())

    elif len(listDuration)>1:
        startindex=0
        currenttasktime = sum(listDuration[startindex:],datetime.timedelta())
    else:
        currenttasktime=datetime.datetime.now()-listStartTime[-1]
   
    

def pause():
    global running
    global pausetime

    root.after_cancel(update_time)
    pausetime=datetime.datetime.now()
    running = False
    if idletime > timeout:        
        autoPause()
    update()


def autoPause():
    global idletime
    global autopause

    idletime=getIdleTime()
    if idletime > timeout:
        autopause = root.after(interval,autoPause)
    else:
        root.after_cancel(autopause)
        start()


def start():
    global running
    global pausetime
    global timerstart

    if pausetime == 0: #new timer
        log() 
        timerstart=datetime.datetime.now()
        running=True
        print("starting new timer")
        update()
    else:
        difference_time = (datetime.datetime.now()-pausetime)
        notify("Resuming after paused for "+humanize.naturaldelta(difference_time)+".")
        timerstart=timerstart+difference_time		
        listPause[-1]=roundTime(difference_time)
        pausetime == 0
        running=True
        update()

def reset():
    """
    Return variables to init and stop logging
    TODO: doest work properly
    """
    global timerstart
    global pausetime
    global totaltime
    global totalpausetime

    listDuration[-1]=roundTime(datetime.datetime.now()-listStartTime[-1])
    timerstart=datetime.datetime.now()
    totalpausetime=datetime.timedelta(0)
    totaltime=datetime.datetime.now()-timerstart

def displayUpdate():
    """
    Handles updating the display of numbers
    """

    if running:
        canvas.itemconfig(displayTime,
        text=str(roundTime(totaltime))
        )
        
        totalcurrenttasktime= currenttasktime+datetime.datetime.now()-listStartTime[-1]
        timecurrenttask = str(roundTime(totalcurrenttasktime))

        canvas.itemconfig(displayTimeTasks,
        text=timecurrenttask
        ) 
    
    if not running:
        canvas.itemconfig(displayPaused,
        text=str(roundTime(totalpausetime))
        )

    nrtasks='{:0>4}'.format(str(len(set(listPlan))))
    canvas.itemconfig(displayNrTasks,
    text=nrtasks
    )
   
        

def saveQuit():
    """
    Finish up logging the activity and pause time if needed.
    Zip data into dataframe and save to file.
    Stop the program.
    """
    if not running and not isinstance(pausetime, int):
        difference_time = roundTime((datetime.datetime.now()-pausetime))
        listPause[-1] = difference_time
    
    if running:
        pause()
        listDuration[-1]=roundTime(datetime.datetime.now()-listStartTime[-1])

    df = pd.DataFrame(list(zip(listPlan, listWindow, listURL, listProcess, listStartTime, listDuration, listPause)),
               columns =['Plan', 'Window', 'URL', 'Software', 'Started', 'Duration', 'Paused'])


    output_path="output.csv"
    try:
        df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
        #buildStats(pd.read_csv(output_path))
    except PermissionError:
        timestring = datetime.datetime.now().strftime("%m%d%Y%H%M%S")
        print("Cannot save, output.csv is currently in use. Using alternative name output"+timestring+".csv")
        df.to_csv(output_path+timestring, mode='a', header=not os.path.exists(output_path+timestring),index=False)  
        #buildStats(pd.read_csv(output_path+timestring))
    
    root.destroy()

def buildStats(data):
    """
    Function to get statistics from output.csv.
    """
    
    groupbyplan=data.groupby(['Plan'])['Duration'].sum()
    df = pd.DataFrame(groupbyplan)


    output_path="stats.csv"
    try:
        df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
    except PermissionError:
        timestring = datetime.datetime.now().strftime("%m%d%Y%H%M%S")
        print("Cannot save, stats.csv is currently in use. Using alternative name output"+timestring+".csv")
        df.to_csv(output_path+timestring, mode='a', header=not os.path.exists(output_path+timestring),index=False)  
 


def switch():
    #switches state between running and paused
    if running:
        startButton.config(image=button_image_2)
        pause()
    else:
        startButton.config(image=button_image_2a)
        start()

def autoLogSwitch():
    global autologging
    if autologging:
        autoLogButton.config(image=button_image_1)
        autologging=False
    else:
        autoLogButton.config(image=button_image_1a)
        autologging=True
    log()

"""
GUI
"""

root.geometry("407x441")
root.title('Moktime')

canvas = Canvas(
    root,
    bg = "#FFFFFF",
    height = 441,
    width = 407,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    136.0,
    281.0,
    image=entry_image_1
)
planEntry = Entry(
    bd=0,
    bg="#BCB9B9",
    highlightthickness=0,
    textvariable=plan
)
planEntry.place(
    x=36.0,
    y=256.0,
    width=200.0,
    height=48.0
)

displayTime = canvas.create_text(
    110.0,
    84.0,
    anchor="nw",
    text="00:00:00",
    fill="#000000",
    font=("CourierPrime Regular", 48 * -1)
)

"""
displaySeconds = canvas.create_text(
    242.0,
    84.0,
    anchor="nw",
    text="00",
    fill="#CD2727",
    font=("CourierPrime Regular", 48 * -1)
)
"""

displayNrTasks = canvas.create_text(
    74.0,
    195.0,
    anchor="nw",
    text="0000",
    fill="#CD2727",
    font=("CourierPrime Regular", 48 * -1)
)

displayPaused = canvas.create_text(
    30.0,
    43.0,
    anchor="nw",
    text="00:00:00",
    fill="#CD2727",
    font=("CourierPrime Regular", 18 * -1)
)

displayTimeTasks = canvas.create_text(
    277.0,
    43.0,
    anchor="nw",
    text="00:00:00",
    fill="#CD2727",
    font=("CourierPrime Regular", 18 * -1)
)

canvas.create_text(
    14.0,
    23.0,
    anchor="nw",
    text="Total Paused",
    fill="#000000",
    font=("CourierPrime Regular", 18 * -1)
)

canvas.create_text(
    257.0,
    23.0,
    anchor="nw",
    text="Current Task",
    fill="#000000",
    font=("CourierPrime Regular", 18 * -1)
)

canvas.create_text(
    64.0,
    151.0,
    anchor="nw",
    text="Number of tasks\nthis session",
    fill="#000000",
    font=("CourierPrime Regular", 18 * -1)
)

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_image_1a = PhotoImage(
    file=relative_to_assets("button_1a.png"))
autoLogButton = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=autoLogSwitch,
    relief="flat"
)
autoLogButton.place(
    x=279.0,
    y=165.0,
    width=87.0,
    height=50.0
)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_image_2a = PhotoImage(
    file=relative_to_assets("button_2a.png"))
startButton = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=switch,
    relief="flat"
)
startButton.place(
    x=157.0,
    y=365.0,
    width=87.0,
    height=50.0
)

"""
resetbutton doesnt work atm


button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
resetButton = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=reset,
    relief="flat"
)
resetButton.place(
    x=36.0,
    y=365.0,
    width=87.0,
    height=50.0
)
"""
button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
quitButton = Button(
    image=button_image_4,
    borderwidth=0,
    highlightthickness=0,
    command=saveQuit,
    relief="flat"
)
quitButton.place(
    x=279.0,
    y=365.0,
    width=87.0,
    height=50.0
)

button_image_5 = PhotoImage(
    file=relative_to_assets("button_5.png"))
planButton = Button(
    image=button_image_5,
    borderwidth=0,
    highlightthickness=0,
    command=log,
    relief="flat"
)
planButton.place(
    x=279.0,
    y=256.0,
    width=87.0,
    height=50.0
)

"""
GLOBAL HOTKEYS
"""
keyboard.add_hotkey('ctrl+space', switch)

"""
MAIN LOOP
"""
root.mainloop()
