#!/usr/bin/env python
import urllib, urllib2
from datetime import datetime

from BeautifulSoup import BeautifulSoup
from dateutil.parser import parse

BASE_URL = 'http://ucilnica.fri.uni-lj.si'
USERNAME = '******@student.uni-lj.si'
PASSWORD = '*****'

def parse_date(date):
	months = [('januar', 'January'), ('februar', 'February'), ('marec', 'March'), ('maj', 'May'), ('junij', 'June'), ('julij', 'July'), ('avgust', 'August'), ('oktober', 'October')]
	date = ' '.join(date.split(',')[1:])
	for month in months:
		date = date.replace(month[0], month[1])
	return parse(date)

# build opener
o = urllib2.build_opener(urllib2.HTTPCookieProcessor())
urllib2.install_opener(o)

# login and get list of courses
p = urllib.urlencode({'username': USERNAME, 'password': PASSWORD})
doc = BeautifulSoup(o.open(BASE_URL.replace('http://', 'https://') + '/login/index.php',  p).read())
courses = [(a.text, dict(a.attrs)['href']) for a in doc.find('h2', text = ['My courses', 'Moji predmeti']).findNext('ul', 'list').findAll('a')]

# generate event list
events = []

for course in courses:
	# check assigments
	doc = BeautifulSoup(o.open(course[1].replace('course/view.php', 'mod/assignment/index.php'),  p).read())
	for assigment in doc.findAll('tr')[1:]: # first is header
		namefield = assigment.find('td', 'c1')
		if namefield: # if not its not actually an assigment
			submittedfield = assigment.find('td', 'c4')
			if not submittedfield.find('span'): # if not already submitted
				datefield = assigment.find('td', 'c3')
				if datefield.text.strip() != '-': # if there is due date
					date = parse_date(datefield.text)
					if date >= datetime.now(): # whtas gone is gone
						events.append((date, course[0], namefield.a.text))
	
	# check quizes
	doc = BeautifulSoup(o.open(course[1].replace('course/view.php', 'mod/quiz/index.php'),  p).read())
	for assigment in doc.findAll('tr')[1:]: # first is header
		namefield = assigment.find('td', 'c1')
		if namefield: # if not its not actually an assigment
			datefield = assigment.find('td', 'c2')
			if datefield.text.strip() != '-': # if there is due date
				date = parse_date(datefield.text)
				if date >= datetime.now(): # whtas gone is gone
					# check if we already solved the quiz
					doc = BeautifulSoup(o.open(BASE_URL + '/mod/quiz/' + dict(namefield.a.attrs)['href'],  p).read())
					if not doc.find('table'):
						events.append((date, course[0], namefield.a.text))

events.sort()
	
# print events
for event in events:
	print '%d days left:' % (event[0] - datetime.now()).days, '%s - %s' % (event[1], event[2])

