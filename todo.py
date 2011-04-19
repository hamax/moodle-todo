#!/usr/bin/env python
import os
import sys
import urllib, urllib2
from datetime import datetime

from BeautifulSoup import BeautifulSoup

BASE_URL = 'http://ucilnica.fri.uni-lj.si'
USERNAME = ''
PASSWORD = ''
SHOW_URL = False

for arg in sys.argv[1:]:
	if arg == '-v' or arg == '--url':
		SHOW_URL = True

def parse_date(date):
	months = {'januar':1, 'january':1, 'februar':2, 'february':2, 'marec':3, 'march':3, 'april':4, 'maj':5, 'may':5, 'junij':6, 'june':6, 'julij':7, 'july':7, 'avgust':8, 'august':8, 'september':9, 'oktober':10, 'october':10, 'november':11, 'december':12}

	date = [a.strip().split(' ') for a in date.lower().split(',')[1:]]
	
	day = date[0][0].replace('.', '')
	month = months[date[0][1]]
	year = date[0][2]
	
	hour, minute = date[1][0].split(':')
	if len(date[1]) > 1:
		hour = int(hour)
		if hour == 12: hour = 0
		if date[1][1] == 'pm': hour += 12 
	
	return datetime(int(year), int(month), int(day), int(hour), int(minute))

# read config
if not BASE_URL or not USERNAME or not PASSWORD:
	try:
		with open(os.environ['HOME'] + '/.moodle-todo.conf') as f:
			for line in f:
				field, value = [a.strip() for a in line.split('=')]
				if field == 'BASE_URL':
					BASE_URL = value
				if field == 'USERNAME':
					USERNAME = value
				if field == 'PASSWORD':
					PASSWORD = value
	except:
		pass
if not BASE_URL or not USERNAME or not PASSWORD:
	print 'Edit todo.py or ~/.moodle-todo.conf to configure todo'
	sys.exit()

# build opener
o = urllib2.build_opener(urllib2.HTTPCookieProcessor())
urllib2.install_opener(o)

# login and get list of courses
p = urllib.urlencode({'username': USERNAME, 'password': PASSWORD})
doc = BeautifulSoup(o.open(BASE_URL.replace('http://', 'https://') + '/login/index.php',  p).read().decode('utf8', 'replace'))
doc = doc.find('h2', text = ['My courses', 'Moji predmeti'])
if not doc:
	print 'Wrong username and password combination (probably)'
	sys.exit()
courses = [(a.text, dict(a.attrs)['href']) for a in doc.findNext('ul', 'list').findAll('a')]

# generate task list
tasks = []
tasks_done = 0
tasks_all = 0

for course in courses:
	# check assigments
	doc = BeautifulSoup(o.open(course[1].replace('course/view.php', 'mod/assignment/index.php'),  p).read().decode('utf8', 'replace'))
	
	table = doc.findAll('tr')
	
	if table:
		#parse headers
		c_namefield = -1
		c_datefield = -1
		c_submittedfield = -1
		for c in range(10):
			field = table[0].find('th', 'c%d' % c)
			if field:
				if field.text.strip() in ['Name', 'Ime']:
					c_namefield = c
				if field.text.strip() in ['Due date', 'Rok za oddajo']:
					c_datefield = c
				if field.text.strip() in ['Submitted', 'Oddano']:
					c_submittedfield = c
		
		for assigment in table[1:]: # first is header
			namefield = assigment.find('td', 'c%d' % c_namefield)
			if namefield: # if not its not actually an assigment
				datefield = assigment.find('td', 'c%d' % c_datefield)
				if datefield.text.strip() not in ['-', '']: # if there is due date
					date = parse_date(datefield.text)
					if date >= datetime.now(): # whats gone is gone
						submittedfield = assigment.find('td', 'c%d' % c_submittedfield)
						if not submittedfield.find('span'): # if not already submitted
							url = BASE_URL + '/mod/assignment/' + dict(namefield.a.attrs)['href']
							tasks.append((date, course[0], namefield.a.text, url))
						else:
							tasks_done += 1
						tasks_all += 1
	
	# check quizes
	doc = BeautifulSoup(o.open(course[1].replace('course/view.php', 'mod/quiz/index.php'),  p).read().decode('utf8', 'replace'))
	
	table = doc.findAll('tr')
	
	if table:
		#parse headers
		c_namefield = -1
		c_datefield = -1
		for c in range(10):
			field = table[0].find('th', 'c%d' % c)
			if field:
				if field.text.strip() in ['Name', 'Ime']:
					c_namefield = c
				if field.text.strip() in ['Quiz closes', 'Kviz se zapre']:
					c_datefield = c
	
		for assigment in table[1:]: # first is header
			namefield = assigment.find('td', 'c%d' % c_namefield)
			if namefield: # if not its not actually an assigment
				datefield = assigment.find('td', 'c%d' % c_datefield)
				if datefield.text.strip() not in ['-', '']: # if there is due date
					date = parse_date(datefield.text)
					if date >= datetime.now(): # whats gone is gone
						# check if we already solved the quiz
						url = BASE_URL + '/mod/quiz/' + dict(namefield.a.attrs)['href']
						doc = BeautifulSoup(o.open(url,  p).read().decode('utf8', 'replace'))
						if not doc.find('td', 'c0'):
							tasks.append((date, course[0], namefield.a.text, url))
						else:
							tasks_done += 1
						tasks_all += 1

tasks.sort()
	
# print tasks
if tasks:
	print '-' * 70
	for task in tasks:
		left = task[0] - datetime.now()
		if left.days > 1:
			break
		print '%.1f hours left:' % (left.days * 24 + float(left.seconds) / 3600), '%s - %s' % (task[1].encode('utf8', 'replace'), task[2].encode('utf8', 'replace'))
		if SHOW_URL: print task[3]
	print '-' * 70
	for task in tasks:
		left = task[0] - datetime.now()
		if left.days <= 1:
			continue
		print '%d days left:' % left.days, '%s - %s' % (task[1].encode('utf8', 'replace'), task[2].encode('utf8', 'replace'))
		if SHOW_URL: print task[3]
	print '-' * 70
	print '%d/%d upcoming tasks done' % (tasks_done, tasks_all)
else:
	print 'Whoa, all (%d) upcoming tasks done!' % tasks_all

