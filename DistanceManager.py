from gpiozero import DistanceSensor

class DistanceManager():	

	def __init__(self):
		self.ultrasonic = DistanceSensor(echo=17, trigger=3)
		self.ultrasonic.threshold_distance = 0.5
		
	def readDistance():
		return ultrasonic.distance