#!/usr/bin/python

import serial
from serial.serialutil import SerialException
import json
import requests
import time
import logging
import os

class Chirp:
	def __init__(self):
		self.chirp = serial.Serial("/dev/ttyACM0",9600)
		#self.confirm_identity()
		self.stats = {}
		# ThingSpeak API key
		self.api_key = os.env["THING_SPEAK_API_KEY"]
		# ThingSpeak update URL
		self.update_url = "https://api.thingspeak.com/update.json"
		# ThingSpeak Channels
		self.channels = { \
			"temperature_celsius" : "field1",\
			"temperature_farenheit" : "field2", \
			"humidity" : "field3", \
			"capacitance" : "field4", \
			"light" : "field5" \
		}
		logging.basicConfig(filename="chirp.log", filemode="w",level=logging.INFO)
	def parse(self):
		try:
			serial_input = self.chirp.readline().strip()
			self.stats = json.loads(serial_input.replace("\\",r"\\"))
			# sanity checking
			try:
				# sometimes the capacitance and light data get swapped,
				# swap with arbitrary thresholds
				if self.stats['capacitance'] > 600 and self.stats['light'] < 1000:
					cap = self.stats['light']
					light = self.stats['capacitance']
					self.stats['capacitance'] = cap
					self.stats['light'] = light
				# Light read wrong, capacitance read right
				elif self.stats['capacitance'] < 600 and self.stats['light'] < 600:
					self.parse()
				# capacitance read wrong
				elif self.stats['capacitance'] > 600 and self.stats['light'] > 600:
					self.parse()
				# Make sure all keys are present
				for key in self.channels.keys(): self.stats[key]
			except KeyError as k:
				logging.warning("Data came in truncated: %s " % (k,))	
				self.parse() 
			except Exception as e:
				logging.error("unknown error in parse(): %s " % (e,))
		except ValueError as e:
			logging.error("Caught Error: %s, Retrying...." % (e,))
			self.parse()
		except SerialException:
			logging.warning("Caught Serial exception trying to read from device, perhaps another is trying to confirm identity")
			time.sleep(10)
			self.parse()
		except Exception as e:
			logging.critical("Unknown error in %s, %s Exiting..." % (self.parse.__name__,e,))
			exit
	def post_stats(self):
		# After setting the Chirp, first read of capacitance is almost always -1
		# skip post if this is the case
		try:
			if self.stats['capacitance'] == -1 or self.stats['light'] == -1:
				return
		except KeyError:
			logging.error("Key Error in %s, take no action" % (self.post_stats.__name__,))
			return

		body = []
		body.append("api_key=%s" % self.api_key)
		for key in self.stats.keys():
				body.append("%s=%s" % (self.channels[key],self.stats[key],))
		body = "&".join(body)
	        req = requests.post(url=self.update_url,data=body)
		logging.info("Status Code: %d, \nStats: %s" % (req.status_code,self.stats,))

	def get_stats(self):
		return str(self.stats)

if __name__ == "__main__":
	chirp = Chirp()
	while 1:
		chirp.parse()
		chirp.post_stats()
