#!/usr/bin/python

import serial
import json
import requests

class Chirp:
	def __init__(self):
		self.ser = serial.Serial('/dev/ttyACM0',9600)
		self.stats = {}
		# ThingSpeak API key
		self.api_key = "PRJUFK9AY5XJPU22"
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
	def parse(self):
		try:
			serial_input = self.ser.readline().strip()
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
				print "Data came in truncated: ",k	
				self.parse() 
			except Exception as e:
				print "unknown error in parse(): ",e
		except ValueError as e:
			print "Caught Error: ",e,"\n Retrying...."
			self.parse()
	def post_stats(self):
		# After setting the Chirp, first read of capacitance is almost always -1
		# skip post if this is the case
		if self.stats['capacitance'] == -1 or self.stats['light'] == -1:
			return

		body = []
		body.append("api_key=%s" % self.api_key)
		for key in self.stats.keys():
				body.append("%s=%s" % (self.channels[key],self.stats[key],))
		body = "&".join(body)
	        req = requests.post(url=self.update_url,data=body)
		print self.stats
		print "Status Code: %d" % req.status_code	

	def get_stats(self):
		return str(self.stats)

if __name__ == "__main__":
	chirp = Chirp()
	while 1:
		chirp.parse()
		chirp.post_stats()
