from gpiozero import DistanceSensor
from math import pi
from datetime import datetime
from VolumeManager import VolumeManager
from FirebaseManager import FirebaseManager
from TwitterManager import TwitterManager
from DistanceManager import DistanceManager
from TemperatureManager import TemperatureManager
import os
import glob
import time
import RPi.GPIO as GPIO
import json
import uuid

try:
	TANK_HEIGHT = 305 # in mm
	MINIMUM_HEIGHT = 77 # in mm
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
		raw_distance = round(distanceManager.read_distance() * 10, 0) # in mm
		fuel_height = int(TANK_HEIGHT - raw_distance) # in mm
		temperature = temperatureManager.read_temp()
		volume = volumeManager.read_volume(current_height = str(fuel_height), current_temp = temperature)
		firebaseManager.update_tank_current_height_and_volume(user['idToken'], fuel_height, volume, refill_id)

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
				twitterManager.postToTwitter("SPBU MariniAna is now normal.")
			print "Fuel Height", fuel_height, "mm"

		time.sleep(1)

except KeyboardInterrupt:
        GPIO.cleanup()

