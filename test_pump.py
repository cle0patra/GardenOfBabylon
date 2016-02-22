#!/usr/bin/python

import serial
import requests
import json
import iso8601
from dateutil import tz
import datetime
import time

class Pump:
	def __init__(self):
		self.pump = serial.Serial('/dev/ttyACM1',9600)
		self.api_key = "UUSBYI66V3MBTS3Q"
		self.sample_size = 5 # To average over
		self.stats = {}
		self.threshold = 275 # Capacitance threshold for watering, 90% dry
	def read_data(self):
		data = requests.get(url='https://api.thingspeak.com/channels/88443/feeds.json?results=%d&api_key=%s' % \
					(self.sample_size,self.api_key,))
		self.stats = json.loads(data.text.replace("\\",r"\\"))
	def calculate_moisture_level(self):
		times = []
		levels = []
		from_zone = tz.gettz('UTC')
		to_zone   = tz.gettz('EST')
		for i in xrange(self.sample_size):
			time = self.stats['feeds'][i]['created_at']
			cap = self.stats['feeds'][i]['field4']
			date = iso8601.parse_date(time)
			date.replace(tzinfo=from_zone)
			date = date.astimezone(to_zone)
			times.append(date)
			levels.append(cap)
		now = datetime.datetime.now().replace(tzinfo=to_zone)
		for time in times:
			if time < now - datetime.timedelta(minutes=2):
				continue
			else:
				print "Need more up to date information."
				return
		total_sum = 0
		for level in levels:
			total_sum += float(level)
		average_capacitance = total_sum / self.sample_size
		if average_capacitance < self.threshold:
			"Need to water, average capacitance: ",average_capacitance
			self.water()
		else:
			print "Soil is hydrated, average_capacitance = ",average_capacitance
	def water(self):
		print "Watering..."
		prompt = self.pump.readline().strip()
		print prompt
		speed = "255" 
		self.pump.write(speed)
		print "Sleeping for 30 seconds..."
		time.sleep(30)

if __name__ == "__main__":
	pump = Pump()
	while 1:
		pump.read_data()
		pump.calculate_moisture_level()
