from pyfcm import FCMNotification
from datetime import datetime
import os
import glob
import time
import pyrebase
import time
import json
import uuid

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

	def update_tank_current_height_and_volume(self, id_token, current_height, current_volume, refill_id):
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
