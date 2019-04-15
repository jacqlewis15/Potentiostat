#!/usr/bin/python

# Jacqueline Lewis
# potentiostat.py

# This file defines a UI and reading system to gather data from a
# Gamry python-controllable potentiostat for many voltage cycles.

# How to set up the potentiostat
#   - Install compatible software (v6.33)
#   - Add authorization code "GLOBAL=2716398216
#   - Update device firmware

# How to set up computer
#   - Install python 2
#   - Add win32com as module to python
#   - After adding module, close and reopen python

import time
import win32com.client as client
import os
import math

from Tkinter import *
import tkFileDialog

####################################
# Graph Class 
####################################

# This class defines a graph object, and draws it.
class Graph(object):

    def __init__(self,xlim,ylim,xaxis,yaxis,points,title,coord):
        self.xlim = xlim # bounds on x data
        self.ylim = ylim # bounds on y data
        self.xaxis = xaxis # x axis label
        self.yaxis = yaxis # y axis label
        self.points = points # data points
        self.title = title # graph title
        self.coord = coord # tkinter graph space edges
        self.margin = 20
        self.limits() # tkinter graph edges
        self.scales() # conversion from data to tkinter space

    # This function determines the edges of the graph in the given
    # tkinter space.
    def limits(self):
        x1,y1,x2,y2 = self.coord
        self.axisLimits = (x1+self.margin*3,y1+self.margin,
            x2-self.margin,y2-self.margin*3)

    # This function determines the scaling factor from data point
    # to tkinter space for graphing.
    def scales(self):
        x1,y1,x2,y2 = self.axisLimits
        LB,UB = self.xlim
        self.xscale = (x2-x1)/float(UB-LB)
        LB,UB = self.ylim
        self.yscale = (y2-y1)/float(UB-LB)

    # This function converts a data point to a coordinate space
    # point.
    def getCoord(self,point):
        x,y = point
        xcoord = (x-self.xlim[0])*self.xscale+self.axisLimits[0]
        ycoord = (self.ylim[1]-y)*self.yscale+self.axisLimits[1]
        return xcoord,ycoord

    # This function converts a coordinate space point to a data
    # point.
    def getPoint(self,point):
        x,y = point
        xcoord = (x-self.axisLimits[0])/self.xscale+self.xlim[0]
        ycoord = self.ylim[1]-(y-self.axisLimits[1])/self.yscale
        return xcoord,ycoord

    # This function adds a new point to the data points.
    def addPoint(self,point):
        self.points.append(point)

    # This function updates the x and y limits of the data,
    # changing the scaling factor.
    def updateLimits(self,xlim,ylim):
        self.xlim = xlim
        self.ylim = ylim
        self.scales()

    # This function determines if a graph is empty.
    def isEmpty(self):
        return self.points == []

    # This function checks if a coordinate point is within 
    # the graph sapce.
    def inGraph(self,x,y):
        return (self.axisLimits[0] < x < self.axisLimits[2] and
            self.axisLimits[1] < y < self.axisLimits[3])

    # This function makes a log graph from a linear graph.
    def makeLogGraph(self, data):
        # This function checks if a point is within bounds.
        def inBound(point):
            x,y = point
            # if the bound isn't set, all points are in
            if data.bound[0] != None:
                if data.lb > x: return False
            if data.bound[1] != None:
                if data.ub < x: return False
            return True
        # This function gets the correct value out of a tuple.
        def getTuple(point,idx):
            return point[idx]
        # This function checks if a value is None.
        def notNone(point):
            x,y = point
            return y != None
        # gets the points in the log graph
        points = filter(notNone, map(yLog, filter(inBound,self.points)))
        ys = map(lambda x: getTuple(x,1), points)
        xs = map(lambda x: getTuple(x,0), points)
        ylow,xlow = min(ys),min(xs)
        yup,xup = max(ys),max(xs)
        # finds the lifetime of the data
        linReg(data,xs,ys)
        return Graph((xlow,xup),(ylow,yup),self.xaxis,self.yaxis,points,
            self.title,self.coord)

    # This function draws the graph.
    def drawGraph(self,canvas):
        canvas.create_rectangle(self.axisLimits,fill="white")
        self.drawAxes(canvas)
        self.drawPoints(canvas)
        self.drawLabels(canvas)

    # This function draws the graph axes, with numberings.
    def drawAxes(self,canvas):

        # y axes, in volts
        xl,yl,xu,yu = self.axisLimits
        # creates horizontal grid lines
        for i in range(5):
            x1,y1 = xl,yl+i*(yu-yl)/4.0
            x2,y2 = xu,yl+i*(yu-yl)/4.0
            # determines graph marking
            val = round(self.ylim[1]-(self.ylim[1]-self.ylim[0])/4.0*i,2)
            canvas.create_line(x1,y1,x2,y2)
            canvas.create_text(self.axisLimits[0]-5,y2,anchor="e",text=str(val))
        
        # x axes, in ns
        xl,yl,xu,yu = self.axisLimits
        # creates vertical grid lines
        for i in range(5):
            x1,y1 = xl+i*(xu-xl)/4.0,yl
            x2,y2 = xl+i*(xu-xl)/4.0,yu
            # determines graph marking
            val = round((self.xlim[0]+(self.xlim[1]-self.xlim[0])/4.0*i),2)
            canvas.create_line(x1,y1,x2,y2)
            canvas.create_text(x2,y2+20,anchor="n",text=str(val))

    # This function draws the points on the graph.
    def drawPoints(self,canvas):
        for point in self.points:
            x,y = self.getCoord(point)
            if y == None: continue
            x1,y1 = x-2,y-2
            x2,y2 = x+2,y+2
            canvas.create_oval(x1,y1,x2,y2,fill="black")

    # This function draws the graph labels.
    def drawLabels(self,canvas):
        x1,y1,x2,y2 = self.coord
        canvas.create_text((x2-x1)/2+x1,y1+5,text=self.title,
            font="Arial 10 bold")
        canvas.create_text((x2-x1)/2+x1,y2-5,text=self.xaxis,
            font = "Arial 8 bold")
        canvas.create_text(x1+5,(y2-y1)/2+y1,text=self.yaxis,
            font = "Arial 8 bold")

####################################
# File functions
####################################

# from 15-112, These functions read/write contents to/from a file.
def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)

def readFile(path):
    with open(path, "rt") as f:
        return f.read()

# This function gets the file name without the whole path, for use in
# the UI.
def trimFileName(fileName):
    return fileName.split("/")[-1].split(".")[0]

# This function allows the user to select an existing folder.
def folderExplorer():
    location = os.getcwd()
    name = tkFileDialog.askdirectory()
    if name == (): name = ""
    return name

# This function allows the user to select an existing text file.
def fileExplorer():
    location = os.getcwd()
    name = tkFileDialog.askopenfilename(initialdir=location,
            title="Select File",filetypes=(("text","*.txt"),("all files","*.*")))
    if name == (): name = ""
    return name

####################################
# UI
####################################

# This function creates a blank current vs. voltage graph.
def initGraph(data):
    return Graph((0,2),(-0.5,0.5),"Voltage (V)",
                "C\nu\nr\nr\ne\nn\nt\n \n(\nu\nA\n)",
        [],"Current vs. Voltage",(data.margin,data.height/2,
        data.width-data.margin,data.height-data.margin))

# This function initializes the potentiostat and waveform data. It is meant
# to be run each time the user starts a run, not just when the file runs.
def initWaveform(data):
    devicelist = client.Dispatch('GamryCOM.GamryDeviceList')
    data.pstat = client.Dispatch('GamryCOM.GamryPstat')
    data.pstat.Init(devicelist.EnumSections()[0])

    data.pstat.Open()

    data.dtaqcpiv=client.Dispatch('GamryCOM.GamryDtaqCpiv')
    data.dtaqcpiv.Init(data.pstat)
    
    data.dataset = []
    data.first = True
    data.cyclesRun = 0

# This function initializes the UI. It is called once per run of the file.
def init(data):

    data.margin = 5
    data.graph = initGraph(data)

    data.sRate = None
    data.cycles = None
    data.array = None

    data.running = False
    data.count = 0

    data.editing = [False]*6
    data.pipe = [False]*6

    data.lastReading = time.time()
    data.bText = [["Folder name","","Sample rate\n(s/sample)",""],
                  ["Signal file","","# Cycles",""],
                  ["File name","","",""]]

# This function stores data from the potentiostat in an internal
# datastructure. The minLength variable is used to ensure that the
# data is stored in a complete array with no out-of-bound access.
def store(data,lst):
    if len(data.dataset) == 0:
        data.dataset.append(lst)
        data.minLength = len(lst)
    else:
        data.dataset.append(lst)
        if len(lst) < data.minLength: data.minLength = len(lst)

# This function gathers and stores the time, voltage, and current
# data from each cycle.
def addData(data,graphPoints,t):
    # time and voltage are only collected the first cycle (identical per cycle) 
    if data.first:
        v = [x for (x,_) in graphPoints]
        store(data,t)
        store(data,v)
        a = [y for (_,y) in graphPoints]
        store(data,a)
    else:
        a = [y for (_,y) in graphPoints]
        store(data,a)

# This function sets the signal to send to the potentiostat.
def setSignal(data):
    # initializes signal to potentiostat
    data.sig=client.Dispatch('GamryCOM.GamrySignalArray')
    if data.first:
        data.sig.Init(data.pstat, 1, data.sRate,
             len(data.array), data.array, 1) 
        data.pstat.SetSignal(data.sig)
        data.pstat.SetCell(1)
    # updates signal to potentiostat
    else:
        data.sig.Init(data.pstat, 1, data.sRate,
             len(data.array), data.array, 1)
        data.sig.Tweak(data.cycles,data.sRate*10,len(data.array),
                       data.array, 0)
        data.pstat.SetSignal(data.sig)

# This function sends the potentiostat signal and waits for the measurement
# to terminate.
#*#*#*#*# data.complete, and try/except may not be necessary
def runSignal(data):
    # ensures no error in reading
    data.complete = False
    try:
        data.dtaqcpiv.Run(True)
    except:
        data.pstat.Close()
        raise

    # waits for the acquisition to complete
    wait = len(data.array)*data.sRate
    time.sleep(wait)

# This function gets the voltage output from the potentiostat and stores
# the acquired data in an internal datastructure.
def getreading(data):

    # if no input is given, use these parameters
    if data.sRate == None: data.sRate = 0.001
    if data.cycles == None: data.cycles = 5
    if data.array == None: data.array = map(lambda x: x/1000.0,range(1000))

    setSignal(data)
    runSignal(data) 

    # collects the data from the potentiostat
    acquired_points = []
    count = 1
    while count > 0:
        count, points = data.dtaqcpiv.Cook(1) 
        acquired_points.extend(zip(*points))

    # returns certain tuple values
    def getXY(tup):
        # (time,current,_,_,voltage,_,_,_,_)
        (_,y,_,_,x,_,_,_,_) = tup
        return x,y
    def getZ(tup):
        (z,_,_,_,_,_,_,_,_) = tup
        return z

    # gathers data for time, voltage, and current
    t = map(getZ, acquired_points)
    graphPoints = map(getXY,acquired_points)

    # stores collected data and completes acquisition
    addData(data,graphPoints,t)
    data.complete = True
    data.cyclesRun += 1

    return graphPoints

# This function gets the full file path.
def getName(data):
    # ensures a path was specified
    if data.bText[0][1] == "" or data.bText[2][1] == "":
        return None
    name = data.bText[0][1] + "/" + data.bText[2][1] + ".txt"
    return name

# This function gathers all stored data and converts it to the
# format of a text file.
def getContents(data):
    contents = ""
    # ensures no out-of-bound array access
    for i in range(data.minLength):
        line = ""
        for j in range(len(data.dataset)):
            line += str(data.dataset[j][i]) + ", "
        contents += line + "\n"
    # removes extra formatting from end of string
    return contents[:-3]

# This function writes all data to the specified file or does nothing
# if there is no data or no specified file.
def save(data):
    if len(data.dataset) == 0: return  
    # write text file
    name = getName(data)
    if name == None: return
    # store data.dataset in file
    contents = getContents(data)  
    writeFile(name, contents)

# This function stops the potentiostat from cycling.
def stop(data):
    data.running = False
    data.complete = True
    try: data.pstat.Close()
    except: pass
    save(data)

# This function reads voltage data from a specified file to use in the
# potentiostat signal, if the file contains valid data.
def convert(data):
    fileName = data.bText[1][1]
    try: 
        contents = readFile(fileName)
        data.array = map(float,contents.split("\n")[:-1])
    except:
        print("invalid file")
        # removes erroneous file from UI
        data.bText[1][1] = ""
        data.array = None

# This function presses the buttons on the UI.
def press(data,idx):
    if idx == 7:
        # starts potentiostat cycles
        if not data.running:
            initWaveform(data)
            data.graph = initGraph(data)
            data.running = True
            data.complete = True
        else: # stops potentiostat cycles
            stop(data)
    # edits the three text boxes
    elif idx in [1,3,4]:
        if True not in data.editing:
            data.editing[idx] = True
    # gets the folder name
    elif idx == 0:
        data.bText[0][1] = folderExplorer()
    # gets the file for voltage data
    elif idx == 2:
        data.bText[1][1] = fileExplorer()
        convert(data)
        
# This function reacts to buttons pressed.
def mousePressed(event,data): 
    bheight = data.height/13 # 4 buttons down
    bwidth = data.width/5 # 4 buttons across
    center = data.width/2
    left = center-bwidth/2
    right = center+bwidth/2

    # starts/stops run 
    if left < event.x < right:
        if 0.5*bheight < event.y < bheight*1.5:
            press(data,7)
    # edits inputs
    if 0.2*bwidth < event.x < data.width-0.2*bwidth:
        col = int((event.x-0.2*bwidth)/(1.2*bwidth))
        row = int((event.y-2*bheight)/(1.5*bheight))
        if row < 0 or col < 0: pass
        elif (col % 2 == 1 and event.x < 1.2*bwidth+col*1.2*bwidth and
            bheight*2 < event.y < 3*bheight+row*1.5*bheight):
                press(data,col//2+2*row)

# This function reacts to key presses.
def keyPressed(event,data): 
    # edits text boxes if in edit mode
    if True not in data.editing: return
    idx = data.editing.index(True)
    # removes the last character
    if event.keysym == "BackSpace":
        data.bText[idx//2][2*(idx%2)+1] = data.bText[idx//2][2*(idx%2)+1][:-1]
    # ends the edit and sets data if valid, else removes characters
    elif event.keysym == "Return":
        if idx == 1 or idx == 3:
            try: # checks if inputs are valid
                tmp1 = float(data.bText[idx//2][2*(idx%2)+1])
                tmp2 = int(tmp1)
            except: tmp1,tmp2 = None,None
            # if not valid input, resets input blocks
            if idx == 1: 
                data.sRate = tmp1
                if data.sRate == None: data.bText[0][3] = ""
            else:
                data.cycles = tmp2
                if data.cycles == None: data.bText[1][3] = ""
        # ends edit mode
        data.editing[idx] = False
        data.pipe = False
    # adds character
    else:
        data.bText[idx//2][2*(idx%2)+1] += event.char

# This function returns the domain and range for an xy-plot.
def ranges(lst):
    xs = map(lambda (x,_): x, lst)
    ys = map(lambda (_,y): y, lst)
    return (min(xs),max(xs)),(min(ys),max(ys))

# This function operates every frame.
def timerFired(data): 
    # gets potentiostat values
    if data.running and data.complete and data.count % 5 == 0: 
        points = getreading(data)
        # for first cycle, sets new graph limits based on data
        if data.first:
            data.graph.points = points
            xlim,ylim = ranges(points)
            data.graph.updateLimits(xlim,ylim)
            data.first = False
        print(data.cyclesRun)
        # stops potentiostat when desired number of cycles is reached
        if data.cycles != None and data.cyclesRun == data.cycles:
            stop(data)
    # editing cursor
    elif data.count % 5 == 0 and True in data.editing:
        data.pipe = not data.pipe
    data.count += 1

# This function converts true/false to a blinking cursor.
def piping(pipe):
    if pipe: return "|"
    return ""

# This function draws the buttons of the UI.
def drawButtons(canvas,data): 
    bheight = data.height/13 # 4 buttons down
    bwidth = data.width/5 # 4 buttons across
    center = data.width/2
    left = center-bwidth/2
    right = center+bwidth/2

    # draws for rows of buttons
    for i in range(4):
        if i == 0: # top row has only the start/stop button
            canvas.create_rectangle(left,bheight/2,right,1.5*bheight,
                fill="white")
            if data.running: text = "Stop"
            else: text = "Start"
            canvas.create_text(left+bwidth/2,bheight,text=text,
                font="Arial 12 bold")
        else: # all other rows have 4 buttons
            for j in range(4):
                canvas.create_rectangle(bwidth*(0.2*(j+1)+j),
                    bheight*(0.5*(i+1)+i),bwidth*(0.2*(j+1)+j+1),
                    bheight*(0.5*(i+1)+i+1),fill="white")
                if j%2 == 1: # these buttons can be edited
                    text = (data.bText[i-1][j] +
                        piping(data.editing[(i-1)*2+j/2] and data.pipe))
                else: text = data.bText[i-1][j]
                # only prints immediate file name to UI (not full path)
                if j == 1: text = trimFileName(text)
                canvas.create_text(bwidth*(0.2*(j+1)+j+0.5),
                    bheight*(0.5*(i+2)+i),text=text,font="Arial 8 bold")

# This function draws the UI every frame.
def redrawAll(canvas,data):
    canvas.create_rectangle(0,0,data.width+5,data.height+5,fill="white")
    canvas.create_rectangle(0,0,data.width+5,data.height/2-10,fill="orange")
    data.graph.drawGraph(canvas)
    drawButtons(canvas,data)


####################################
# runUI function # from 15-112 #
####################################

def runUI(width=300, height=300):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        redrawAll(canvas, data)
        canvas.update()    

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 50 # milliseconds
    init(data)
    # create the root and the canvas
    root = Tk()
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed
    # closes connection to potentiostat if still open
    try: data.pstat.Close()
    except: pass
        
# dimensions set for Windows XP Dell computer
runUI(600,400)
