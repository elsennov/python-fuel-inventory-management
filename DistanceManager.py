from gpiozero import DistanceSensor
from datetime import datetime
import os
import glob
import time
import RPi.GPIO as GPIO
import time

class DistanceManager():	
	#Set GPIO pin numbering                          
	GPIO.setmode(GPIO.BCM)                     

	#Associate pin 3 to TRIG
	TRIG = 3   
	#Associate pin 17 to ECHO                                
	ECHO = 17                                  

	#Set pin as GPIO out
	GPIO.setup(TRIG,GPIO.OUT) 
	#Set pin as GPIO in                 
	GPIO.setup(ECHO,GPIO.IN)
		
	def read_distance(self):
		#Set TRIG as LOW
	 	GPIO.output(DistanceManager.TRIG, False)
		#Set TRIG as HIGH
		GPIO.output(DistanceManager.TRIG, True)
		#Delay of 0.00001 seconds
		time.sleep(0.00001)                      
		#Set TRIG as LOW
		GPIO.output(DistanceManager.TRIG, False)                 

		#Check whether the ECHO is LOW
		while GPIO.input(DistanceManager.ECHO)==0:               
			#Saves the last known time of LOW pulse
			pulse_start = time.time()

		#Check whether the ECHO is HIGH
		while GPIO.input(DistanceManager.ECHO)==1:               
			#Saves the last known time of HIGH pulse 
			pulse_end = time.time()

		#Get pulse duration to a variable
		pulse_duration = pulse_end - pulse_start

		#Multiply pulse duration by 17150 to get distance
		distance = pulse_duration * 17150
		#Round to two decimal points
		distance = round(distance, 1)

		#Check whether the distance is within range
		if distance > 2 and distance < 400:      
			#Print distance with 0.5 cm calibration
			return distance - 0.5
		else:
			#display out of range
			return -1
