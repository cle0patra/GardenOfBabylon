#!/usr/bin/python

import serial
import requests
import json
import iso8601
from dateutil import tz
import datetime
import time
import logging

#======================================================
#  class Pump:
#	@note: Pumps at 100ml/125s at max speed (255)
#======================================================
class Pump:
	def __init__(self):
		self.pump = serial.Serial("/dev/ttyACM1",9600)
		self.api_key = "UUSBYI66V3MBTS3Q"
		self.sample_size = 5 # To average over
		self.stats = {}
		self.threshold = 275 # Capacitance threshold for watering, 90% dry
		self.target = 350 # Target capacitance after watering
		# ThingSpeak API key
                self.update_api_key = "PRJUFK9AY5XJPU22"
                # ThingSpeak update URL
                self.update_url = "https://api.thingspeak.com/update.json"
		logging.basicConfig(filename="pump.log",filemode="w",level=logging.INFO)
	def read_data(self):
		data = requests.get(url='https://api.thingspeak.com/channels/88443/feeds.json?results=%d&api_key=%s' % \
					(self.sample_size,self.api_key,))
		self.stats = json.loads(data.text.replace("\\",r"\\"))
	def calculate_moisture_level(self):
		self.read_data()
		sensor_data = {"times":[], "levels":[] , "entry_ids" : [] }
		from_zone = tz.gettz('UTC')
		to_zone   = tz.gettz('EST')
		for i in xrange(self.sample_size):
			time = self.stats['feeds'][i]['created_at']
			cap = self.stats['feeds'][i]['field4']
			entry_id = self.stats['feeds'][i]["entry_id"]
			date = iso8601.parse_date(time)
			date.replace(tzinfo=from_zone)
			date = date.astimezone(to_zone)
			sensor_data["times"].append(date)
			sensor_data["levels"].append(cap)
			sensor_data["entry_ids"].append(entry_id)
		now = datetime.datetime.now().replace(tzinfo=to_zone)
		for time in sensor_data["times"]:
			if time < now - datetime.timedelta(minutes=2):
				continue
			else:
				logging.warning("Need more up to date information.")
				return
		total_sum = 0
		for level in sensor_data["levels"]:
			total_sum += float(level)
		average_capacitance = total_sum / self.sample_size
		return average_capacitance,sensor_data
	#================================================
	# @water:
	#	@param speed: Speed at which to run pump
	#	@param seconds: Seconds to pump
	#================================================
	def water(self,speed,seconds):
		params = {}
		params["speed"] = speed
		params["seconds"] = seconds
		command_string = json.dumps(params)
		logging.debug("Command string: %s " % (command_string, ))
		self.pump.write(command_string)
		#time.sleep(seconds)
	#===============================================
	# @post_stats:
	#	@param time_watered: In seconds
	#	@param amount_watered: In milliliters
	#==============================================
	def post_stats(self,time_watered,amount_watered):
		body = []
		body.append("api_key=%s" % (self.update_api_key,))
		body.append("time_watered_seconds=%d" % (time_watered,))
		body.append("amount_watered_milliliters=%d" % (amount_watered,))
		body = "&".join(body)
		req = requests.post(url=self.update_url,data=body)
		logging.info("posted watering data. Response code: %d, body: %s" % (req.status_code,body,))
if __name__ == "__main__":
	pump = Pump()
	while 1:

		cap,sensor_data = pump.calculate_moisture_level()
		logging.info("Capacitance: %d , Sensor Data: %s " % (cap, sensor_data, ))
		newest_old_entry_id = sensor_data["entry_ids"][-1]
		if cap < pump.threshold:
			total_watered = 0
			total_time = 0
			logging.info("cap less than threshold")
			while cap < pump.target:
				pump.water(255,31.25) # Water 25ml at a time
				total_watered += 25
				total_time += 31.25
				new_cap,new_sensor_data = pump.calculate_moisture_level()
				while new_sensor_data["entry_ids"][0] <= newest_old_entry_id: # Wait for a new buffer of sensor data
					new_cap,new_sensor_data = pump.calculate_moisture_level()
				newest_old_entry_id = new_sensor_data["entry_ids"][-1]
				cap = new_cap	
				logging.debug("New Cap: %d, New Sensor Data: %s " % (cap,new_sensor_data,))	
				if cap >= pump.target:
					logging.info("Hit target %d, capacitance = %d" % (pump.target, cap, ))
					logging.info("Total time (ms): %d, Total amount (ml): %d" % (total_time,total_watered,))
					pump.post_stats(total_time,total_watered)
