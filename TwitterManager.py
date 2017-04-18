from datetime import datetime
import os
import glob
import time
import json
import uuid
import twitter
import pytz

class TwitterManager():
	api = twitter.Api(consumer_key='TVy7LrO06dsl7s7LgrtCohBWi',
                      consumer_secret='N5Qc8ULhEb6zmC7MZxzAKPduAsEh9Y65vxRX5Sy9nQfshKyHDL',
                      access_token_key='853745008972677121-q3B481Ypwz1SswFPSn5OQlHZgYRMadW',
                      access_token_secret='JCcPEJ1VReuh63svwhiiGtx4CfuDdTQbc3pxJuEYDF5ue')

	previous_tweet = ""

	def postToTwitter(self, tweet):
		tz = pytz.timezone('Asia/Jakarta')
		now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
		new_tweet = tweet + " (" + now + ")"

		if TwitterManager.previous_tweet != new_tweet:
			status = TwitterManager.api.PostUpdate(new_tweet)
			return status.text
		else:
			return tweet