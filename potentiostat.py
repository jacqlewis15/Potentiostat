#!/usr/bin/python

# How to set up the pi
# From Menu -> Preferences -> Raspberry Pi Configuration -> Interfaces
#	Enable i2c
# edit /etc/rc.local
# 	Add line before exit 0
#		echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined
#	Reboot 


import time
import smbus
from smbus import SMBus
import sys

from Tkinter import *

class Graph(object):

    def __init__(self,xlim,ylim,xaxis,yaxis,points,title,coord):
        self.xlim = xlim
        self.ylim = ylim
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.points = points
        self.title = title
        self.coord = coord
        self.margin = 20
        self.limits()
        self.scales()

    def limits(self):
        x1,y1,x2,y2 = self.coord
        self.axisLimits = (x1+self.margin,y1+self.margin,
            x2-self.margin,y2-self.margin)

    def scales(self):
        x1,y1,x2,y2 = self.coord
        LB,UB = self.xlim
        self.xscale = (x2-x1-2*self.margin)/float(UB-LB)
        LB,UB = self.ylim
        self.yscale = (y2-y1-2*self.margin)/float(UB-LB)

    def getCoord(self,point):
        x,y = point
        xcoord = (x-self.xlim[0])*self.xscale+self.axisLimits[0]
        ycoord = (self.ylim[1]-y)*self.yscale+self.axisLimits[1]
        return xcoord,ycoord

    def addPoint(self,point):
        self.points.append(point)

    def updateLimits(self,xlim,ylim):
        self.xlim = xlim
        self.ylim = ylim

    def drawGraph(self,canvas):
        self.drawAxes(canvas)
        self.drawPoints(canvas)
        self.drawLabels(canvas)

    def drawAxes(self,canvas):
        # axes should be fixed so that non-0 containing are still labelled
        # assumes 0 is center, not always true
        if self.xlim[0] < 0 < self.xlim[1]:
            x1,y1 = self.getCoord((0,self.ylim[0]))
            x2,y2 = self.getCoord((0,self.ylim[1]))
            canvas.create_line(x1,y1,x2,y2)
            xl,yl,xu,yu = self.axisLimits
            for i in range(5):
                x1,y1 = (xu-xl)/2+xl-5,yl+i*(yu-yl)/4
                x2,y2 = (xu-xl)/2+xl+5,yl+i*(yu-yl)/4
                val = self.ylim[1]-(self.ylim[1]-self.ylim[0])/4*i
                canvas.create_line(x1,y1,x2,y2)
                canvas.create_text(x2+5,y2,anchor="w",text=str(val))
        else:
            x1,y1 = self.getCoord((self.xlim[0],self.ylim[0]))
            x2,y2 = self.getCoord((self.xlim[0],self.ylim[1]))
            canvas.create_line(x1,y1,x2,y2)
        if self.ylim[0] < 0 < self.ylim[1]:
            x1,y1 = self.getCoord((self.xlim[0],0))
            x2,y2 = self.getCoord((self.xlim[1],0))
            canvas.create_line(x1,y1,x2,y2)
            xl,yl,xu,yu = self.axisLimits
            for i in range(5):
                x1,y1 = xl+i*(xu-xl)/4,(yu-yl)/2+yl-5
                x2,y2 = xl+i*(xu-xl)/4,(yu-yl)/2+yl+5
                val = self.xlim[0]+(self.xlim[1]-self.xlim[0])/4.0*i
                canvas.create_line(x1,y1,x2,y2)
                canvas.create_text(x2,y2+20,anchor="n",text=str(val),angle=90)
        else:
            x1,y1 = self.getCoord((self.xlim[0],self.ylim[0]))
            x2,y2 = self.getCoord((self.xlim[1],self.ylim[0]))
            canvas.create_line(x1,y1,x2,y2)

    def drawPoints(self,canvas):
        for point in self.points:
            x,y = self.getCoord(point)
            x1,y1 = x-2,y-2
            x2,y2 = x+2,y+2
            canvas.create_oval(x1,y1,x2,y2,fill="black")

    def drawLabels(self,canvas):
        x1,y1,x2,y2 = self.coord
        canvas.create_text((x2-x1)/2+x1,y1+5,text=self.title,font="Arial 15 bold")
        canvas.create_text((x2-x1)/2+x1,y2-5,text=self.xaxis,font = "Arial 12 bold")
        canvas.create_text(x1+5,(y2-y1)/2+y1,text=self.yaxis,font = "Arial 12 bold",angle=90)


####################################
# UI
####################################

def initGraph(data):
	return Graph((-2.5,2.5),(-400,400),"Voltage (V)","Current (uA)",
		[],"Current vs. Voltage",(data.margin,data.height/2,
		data.width-data.margin,data.height-data.margin))

def getreading(data,adc_address,adc_channel):
	data.bus.write_byte(adc_address, adc_channel)
	time.sleep(data.restTime)
	reading = data.bus.read_i2c_block_data(adc_address, adc_channel, data.numBytes)
	sign = (reading[0]&0x40)>>6
	raw = (((reading[0]&0x3F)<<16)+(reading[1]<<8)+(reading[2]&0xC0))>>6
	print(reading)
	volts = raw/65536.0*data.vref
	return (volts-data.vref) if sign else volts

# while(True):
# 	Ch0value = getreading(address, channel0)
# 	time.sleep(restTime)
# 	Ch2value = 200*getreading(address, channel2) # depends on gain
# 	print("Voltage %2.2f, Current %2.2f\n" % (Ch0value, Ch2value))
# 	time.sleep(restTime)
# 	sys.stdout.flush()
# 	time.sleep(measTime)

def init(data):
	data.margin = 5
	data.graph = initGraph(data)
	data.bus = SMBus(1)

	data.address = 0b1110110 # HIGH HIGH HIGH 0x76

	data.channels = [0xA0,0xA1]

	data.vref = 2.5

	data.numBytes = 3
	# data.measTime = 0.2
	data.restTime = 0.15

	data.lastReading = time.time()

def mousePressed(event,data): pass

def keyPressed(event,data): pass

def timerFired(data): 
	# if time.time()-data.lastReading > data.measTime:
	Ch0value = getreading(data, data.address, data.channels[0])
	time.sleep(data.restTime)
	Ch2value = 200*getreading(data, data.address, data.channels[1]) # depends on gain
	# print("Voltage %2.2f, Current %2.2f\n" % (Ch0value, Ch2value))
	data.graph.addPoint((Ch0value,Ch2value))
	time.sleep(data.restTime)
	sys.stdout.flush()

def redrawAll(canvas,data):
	data.graph.drawGraph(canvas)


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
    data.timerDelay = 100 # milliseconds
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

runUI(800,800)