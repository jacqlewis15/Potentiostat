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

import matplotlib.pyplot as plt

bus = SMBus(1)

address = 0b1110110 # HIGH HIGH HIGH 0x76

channel0 = 0xA0
channel2 = 0xA1

vref = 2.5

numBytes = 6
measTime = 0.5
restTime = 0.4

xs = []
ys = []

plt.ion()
# plt.show()
fig = plt.figure()
ax = fig.add_subplot(1,1,1)
line, = ax.plot(xs,ys)

############ Find resistances to stop raspberry pi from breaking the potentiostat

def getreading(adc_address,adc_channel):
 	bus.write_byte(adc_address, adc_channel)
 	time.sleep(restTime)
 	reading = bus.read_i2c_block_data(adc_address, adc_channel, numBytes)
 	sign = (reading[0]&0x40)>>6
 	raw = (((reading[0]&0x3F)<<16)+(reading[1]<<8)+(reading[2]&0xC0))>>6
 	volts = raw/65536.0*vref
 	return (volts-vref) if sign else volts

def updateGraph(x,y):
	xs.append(x)
	ys.append(y)
	line.set_xdata(xs)
	line.set_ydata(ys)
	fig.canvas.draw()
	plt.show()

time.sleep(restTime)
ch0_mult = 1

while(True):
	Ch0value =  ch0_mult*getreading(address, channel0)
	# Ch0value = 1.0
	time.sleep(restTime)
	Ch2value = 200*getreading(address, channel2) # depends on gain
	print("Voltage %2.2f, Current %2.2f\n" % (Ch0value, Ch2value))
	updateGraph(round(Ch0value,2),round(Ch2value,2))
	# print ("Voltage: %12.2f   Current: %12.2f" % (Ch0value, Ch2value))
	time.sleep(restTime)
	sys.stdout.flush()
	time.sleep(measTime)


##### Currently not giving correct readings....