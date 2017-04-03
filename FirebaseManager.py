import pyrebase

class FirebaseManager():
		
	config = {
	  "apiKey": "AIzaSyBJlla7o3Vac0mrVffWQqW01V6w5L7tEgc",
	  "authDomain": "fuelinventorymanagement.firebaseapp.com",
	  "databaseURL": "https://fuelinventorymanagement.firebaseio.com",
	  "storageBucket": "fuelinventorymanagement.appspot.com"
	}

	firebase = pyrebase.initialize_app(config)