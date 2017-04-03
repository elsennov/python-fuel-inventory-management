from gpiozero import DistanceSensor
from pyfcm import FCMNotification
import os
import glob
import time
import pyrebase
import RPi.GPIO as GPIO
import time
import json
import uuid

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
		distance = round(distance, 2)            

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
	    f = open(device_file, 'r')
	    lines = f.readlines()
	    f.close()
	    return lines
	 
	def read_temp(self):
	    lines = read_temp_raw()
	    while lines[0].strip()[-3:] != 'YES':
	        time.sleep(0.2)
	        lines = read_temp_raw()
	    equals_pos = lines[1].find('t=')
	    if equals_pos != -1:
	        temp_string = lines[1][equals_pos+2:]
	        temp_c = float(temp_string) / 1000.0
	        temp_f = temp_c * 9.0 / 5.0 + 32.0
	        return str(temp_c)+'C', str(temp_f)+'F'

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

	def update_tank_current_height(self, id_token, current_height):
		tank = {
			"current_height":current_height,
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
	current_millis_time = lambda: int(round(time.time() * 1000))

	firebaseManager = FirebaseManager()
	user = firebaseManager.sign_in_with_email_and_password("novraditya@gmail.com", "password")
	user_registration_id = firebaseManager.get_user_registration_id(user['idToken'], user['localId'])

	distanceManager = DistanceManager()
	refill_id = ""

	while True:
		distance = distanceManager.read_distance()
		firebaseManager.update_tank_current_height(user['idToken'], distance)

		refill_map = firebaseManager.get_latest_refill(user['idToken'], refill_id)
		if refill_map == None:
			notified = False
		else:
			notified = firebaseManager.is_already_notified(refill_map['refill'])
		print "Notified: ",notified
		
		if distance <= 3 and not notified:
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
			
			print "Low fuel!"
		else:
			print "Distance", distance, "cm"

		time.sleep(1)

except KeyboardInterrupt:
        GPIO.cleanup()

