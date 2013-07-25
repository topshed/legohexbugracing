#!/usr/bin/python

import serial
import time
import sqlite3
import RPi.GPIO as GPIO
import scratch


TAGS = {'DC6':True, 'C66':True,'305':True,'6C7':True,'E93':True}
PLACES = {'DC6':(None,None), 'C66':(None,None),'305':(None,None),'6C7':(None,None),'E93':(None,None)}


TAGmini1 = '4D004A8DC6'
TAGmini2 = '4D004A7C66'
TAGmini3 = '4D004A7305'
TAGcircle = '0700B8E462'
TAGmini4 = '4D004A86C7'
TAGmini5 = '4D004A8E93'
TAGmini6 = '4D004A8D9D'
TAGfob = '8400355F2C'
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16,GPIO.IN)
s = scratch.Scratch()
fastestEver = 0

def listen():

  print 'waiting'
	msg = {}
	msg['broadcast'] = None
	while msg['broadcast'] != ['Racing']:
		msg = s.receive()
	main()
	
	
def race():
	TAGS = {'DC6':True, 'C66':True,'305':True,'6C7':True,'E93':True}
	ser = serial.Serial('/dev/ttyUSB0', 2400, timeout=1)
	start =time.time()
	position = 1
	conn = sqlite3.connect("test.db")
	cur = conn.cursor()
	while position < 6:
			string = ser.read(12)
			print string
			if len(string) != 0:
				   # if string == '4D004A8DC6':
					string = string[1:11]
					tag = string[-3:]
					print 'seen ' + tag
					end = time.time()
					print end-start
					lap = round(end-start,3)
					if TAGS[tag]:
						print 'updating dict for ' + tag
						PLACES[tag]=(position,lap)
						position=position+1
						print 'incrementing position to ' + str(position)
						TAGS[tag] = False
						msgString = tag + 'Finished'
						s.broadcast('msgString')
					else:
						print 'already seen ' + tag
	ser.close()
	print PLACES
	for key,values in PLACES.items():
		print 'updating '  + key
		points = 6 - values[0]
		cur.execute("SELECT min(fastest) from testrace")
		fastestEver = cur.fetchone()
		print 'Lap record is ' + str(fastestEver[0])
		cur.execute("UPDATE testrace SET points=points + ? where tag=?",[points,key])
		cur.execute("UPDATE testrace SET races=races + 1 where tag=?",[key])
		if values[0] == 1:
			cur.execute("UPDATE testrace SET victories=victories + 1 where tag=?",[key])
		cur.execute("SELECT fastest from testrace where tag=?", [key])
		fastsofar = cur.fetchone()
		if values[1] < fastestEver[0]:
			print "New lap record"
			s.broadcast('RecordTime')
		print 'fastest so far ' + str(fastsofar[0])
		if (fastsofar[0] == 0) or (fastsofar[0] > values[1]):
			cur.execute("UPDATE testrace SET fastest=? where tag=?",[values[1],key])
		#cur.execute("UPDATE testrace SET victories=victories + 1 where tag=?",[tag])
		
	conn.commit()
	conn.close()
	return(PLACES)
	
def resultsToScratch(PLACES):
	results = {}
	winner = None
	second = None
	third = None
	for key,values in PLACES.items():
		if values[0] == 1:
			winner = key
		if values[0] == 2:
			second = key
		if values[0] == 3:
			third = key
	results['winner'] = winner
	results['second'] = second
	results['third'] = third
	s.sensorupdate(results)
	s.broadcast('RaceEnd')
	
def scoreboardToScratch(PLACES):

	data = {}
	conn = sqlite3.connect("test.db")
	cur = conn.cursor()
	for key,values in PLACES.items():
		tag_fast = key + '_fast'
		cur.execute("SELECT fastest from testrace where tag=?", [key])
		fastsofar = cur.fetchone()
		data[tag_fast] = str(fastsofar[0])
		tag_pts = key + '_pts'
		cur.execute("SELECT points from testrace where tag=?", [key])
		pts = cur.fetchone()
		data[tag_pts] = str(pts[0])
		tag_races = key + '_races'
		cur.execute("SELECT races from testrace where tag=?", [key])
		races = cur.fetchone()
		data[tag_races] = str(races[0])
		tag_vic = key + '_vic'
		cur.execute("SELECT victories from testrace where tag=?", [key])
		vic = cur.fetchone()
		data[tag_vic] = str(vic[0])
	s.sensorupdate(data)
	s.broadcast('PythonMsg')
	
	conn.close()
	
def main():
	GPIO.wait_for_edge(16,GPIO.FALLING)
	print 'starting race'
	s.broadcast('start')
	racePlaces = race()
	print 'sending results to scratch'
	resultsToScratch(racePlaces)
	print 'sending scoreboard to scratch'
	scoreboardToScratch(racePlaces)
	print 'end of race'
	listen()
	
listen()
