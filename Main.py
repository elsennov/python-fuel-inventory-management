from gpiozero import DistanceSensor
from pyfcm import FCMNotification
from math import pi
from datetime import datetime
import os
import glob
import time
import pyrebase
import RPi.GPIO as GPIO
import time
import json
import uuid
import twitter

class TwitterManager():
	api = twitter.Api(consumer_key='TVy7LrO06dsl7s7LgrtCohBWi',
                      consumer_secret='N5Qc8ULhEb6zmC7MZxzAKPduAsEh9Y65vxRX5Sy9nQfshKyHDL',
                      access_token_key='853745008972677121-q3B481Ypwz1SswFPSn5OQlHZgYRMadW',
                      access_token_secret='JCcPEJ1VReuh63svwhiiGtx4CfuDdTQbc3pxJuEYDF5ue')

	previous_tweet = ""

	def postToTwitter(self, tweet):
		now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		new_tweet = tweet + " (" + now + ")"

		if TwitterManager.previous_tweet != new_tweet:
			status = TwitterManager.api.PostUpdate(new_tweet)
			return status.text
		else:
			return tweet

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
 
class TemperatureManager():
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')
	 
	base_dir = '/sys/bus/w1/devices/'
	device_folder = glob.glob(base_dir + '28*')[0]
	device_file = device_folder + '/w1_slave'
 
	def read_temp_raw(self):
	    f = open(TemperatureManager.device_file, 'r')
	    lines = f.readlines()
	    f.close()
	    return lines
	 
	def read_temp(self):
	    lines = self.read_temp_raw()
	    while lines[0].strip()[-3:] != 'YES':
	        time.sleep(0.2)
	        lines = read_temp_raw()
	    equals_pos = lines[1].find('t=')
	    if equals_pos != -1:
	        temp_string = lines[1][equals_pos+2:]
	        temp_c = float(temp_string) / 1000.0
	        # temp_f = temp_c * 9.0 / 5.0 + 32.0
	        return temp_c

class VolumeManager():

	average_base_area = 8.14057038673254

	# current_height in cm
	# current_temp in C
	def read_volume(self, current_height, current_temp):
		raw_volume = pi * (VolumeManager.average_base_area * VolumeManager.average_base_area) * current_height
		volume = raw_volume * (1 + (0.00045 * (current_temp - 27)))
		return round(volume, 1)

class FirebaseManager():
	config = {
	  "apiKey": "AIzaSyBJlla7o3Vac0mrVffWQqW01V6w5L7tEgc",
	  "authDomain": "fuelinventorymanagement.firebaseapp.com",
	  "databaseURL": "https://fuelinventorymanagement.firebaseio.com",
	  "storageBucket": "fuelinventorymanagement.appspot.com"
	}

	firebase = pyrebase.initialize_app(config)
	push_service = FCMNotification(api_key="AAAAr-d53Zg:APA91bGtH89IdY7U37nK1oZMXt7SXGxHVzuy5m-Wjuy9GujASz9uQVsoFXKe7LQV-Q6YifEVpw_v1bU6uCAuV-Q6KYefWQ8x_9VBI4e0rTcFOLbgsuPLpYOKfUa6a-QzoIo1ouMSUqBj")
	tank_id = "792bb88d-7e39-47af-86f7-b0f84d132e4e"

	def sign_in_with_email_and_password(self, email, password):
		return FirebaseManager.firebase.auth().sign_in_with_email_and_password(email, password)

	def get_user_registration_id(self, id_token, local_id):
		user_registration_id_obj = FirebaseManager.firebase.database().child("registration_ids").child(local_id).get(id_token)
		return user_registration_id_obj.val()['registration_id']

	def update_tank_current_height_and_volume(self, id_token, current_height, current_volume):
		tank = {
			"current_height":current_height,
			"current_volume":current_volume,
			"updated_at":int(round(time.time() * 1000))
		}
		
		tank_ref = FirebaseManager.firebase.database().child("tanks").child(FirebaseManager.tank_id)
		result = tank_ref.set(tank, id_token)
		return {
			"refill_id":refill_id,
			"refill": result
		}

	def get_latest_refill(self, id_token, refill_id=""):
		refills = FirebaseManager.firebase.database().child("refills").order_by_key().get(id_token).val()
		
		if refills == None:
			return None

		if refill_id == "":
			refill_id = refills.keys()[0]

		return {
			"refill_id": refill_id,
			"refill": refills[refill_id]
		}

	def is_already_notified(self, refill):
		if refill['status'] == 'requested':
			return True

		if refill['status'] == 'notified' and not self.is_notification_expired(refill['updated_at']):
			return True

		return False

	# Expired means the last_update_time is more than 5 hours
	def is_notification_expired(self, last_update_time):
		current_millis_time = int(round(time.time() * 1000))
		elapsed_time = current_millis_time - last_update_time
		return elapsed_time > 10000

	def send_notification(self, registration_id, data_message):
		return FirebaseManager.push_service.notify_single_device(
			registration_id=registration_id, 
			data_message=data_message
		)

	def notify_to_refill(self, id_token, refill_map, updated_at = 0):
		refill_notification = {
			"status":"notified",
			"updated_at":updated_at
		}
		
		if refill_map == None:
			refill_id = str(int(round(time.time() * 1000)))
		elif refill_map['refill']['status'] == 'notified':
			refill_id = refill_map['refill_id']
		else:
			refill_id = str(int(round(time.time() * 1000)))

		refill_ref = FirebaseManager.firebase.database().child("refills").child(refill_id)
		result = refill_ref.set(refill_notification, id_token)
		return {
			"refill_id":refill_id,
			"refill": result
		}

try:
	TANK_HEIGHT = 30.5 # in CM
	MINIMUM_HEIGHT = 7.7 # in CM
	current_millis_time = lambda: int(round(time.time() * 1000))

	firebaseManager = FirebaseManager()
	user = firebaseManager.sign_in_with_email_and_password("novraditya@gmail.com", "password")
	user_registration_id = firebaseManager.get_user_registration_id(user['idToken'], user['localId'])

	refill_id = ""
	current_status = "low"

	distanceManager = DistanceManager()
	temperatureManager = TemperatureManager()
	volumeManager = VolumeManager()
	twitterManager = TwitterManager()

	while True:
		raw_distance = distanceManager.read_distance()
		fuel_height = TANK_HEIGHT - raw_distance
		temperature = temperatureManager.read_temp()
		volume = volumeManager.read_volume(current_height = fuel_height, current_temp = temperature)
		firebaseManager.update_tank_current_height_and_volume(user['idToken'], fuel_height, volume)

		refill_map = firebaseManager.get_latest_refill(user['idToken'], refill_id)
		if refill_map == None:
			notified = False
		else:
			notified = firebaseManager.is_already_notified(refill_map['refill'])
		print "Notified: ",notified
		
		if fuel_height <= MINIMUM_HEIGHT and not notified:
			# Update database
			result = firebaseManager.notify_to_refill(id_token=user['idToken'], refill_map=refill_map, updated_at=current_millis_time())
			refill_id = result['refill_id']
			print result

			# Send notification
			data_message = {
				"refill_id": refill_id
			}	
			result = firebaseManager.send_notification(
				registration_id = user_registration_id,
				data_message = data_message
			)

			# Post to twitter
			current_status = "low"
			twitterManager.postToTwitter("SPBU MariniAna is currently low of fuel.")

			print "Low fuel!"
		else:
			if current_status == "low" and fuel_height > MINIMUM_HEIGHT:
				current_status = "normal"
				twitterManager.postToTwitter("SPBU MariniAna is currently normal.")
			print "Fuel Height", fuel_height, "cm"

		time.sleep(1)

except KeyboardInterrupt:
        GPIO.cleanup()

