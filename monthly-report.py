#!/usr/local/bin/python3.7

import yaml
import traceback
import datetime
import requests
import smtplib

from bs4 import BeautifulSoup
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid

def main():
	#
	# Load configuration
	with open('config.yaml', 'r') as configFile:
		try:
			config = yaml.safe_load(configFile)
		except:
			traceback.print_exc()
			print("ERROR: could not load config.yaml")
	#
	# Datermine the applicable date range: the previous month
	today = datetime.date.today()
	endDate = today.replace(day=1) - datetime.timedelta(days=1)
	startDate = endDate.replace(day=1)
	#
	# Set us up for API requests
	HEADERS = {'Authorization': 'Bearer {}'.format(config['accesstoken'])}
	with requests.Session() as s:
		s.headers.update(HEADERS)
		#
		# Get all the categories
		url = config['firefly-url'] + '/api/v1/categories'
		categories = s.get(url).json()
		#
		# Get the spent and earned totals for each category
		totals = []
		for category in categories['data']:
			url = config['firefly-url'] + '/api/v1/categories/' + category['id'] + '?start=' + startDate.strftime('%Y-%m-%d') + '&end=' + endDate.strftime('%Y-%m-%d')
			r = s.get(url).json()
			categoryName   = r['data']['attributes']['name']
			try:
				categorySpent  = r['data']['attributes']['spent'][0]['sum']
			except (KeyError, IndexError):
				categorySpent = 0
			try:
				categoryEarned = r['data']['attributes']['earned'][0]['sum']
			except (KeyError, IndexError):
				categoryEarned = 0
			categoryTotal  = float(categoryEarned) + float(categorySpent)
			totals.append( {'name': categoryName, 'spent': categorySpent, 'earned': categoryEarned, 'total': categoryTotal} )
		# Set up the email body
		msg = EmailMessage()
		msg['Subject'] = "Firefly III: Monthly categories report"
		msg['From'] = "monthly-report <" + config['email']['from'] + ">"
		msg['To'] = ( tuple(config['email']['to']) )
		#tableBody = '<table><tr><th>Category</th><th>Spent</th><th>Earned</th><th>Total</th></tr>'
		tableBody = '<table><tr><th>Category</th><th>Total</th></tr>'
		for category in totals:
			#tableBody += '<tr><td>'+category['name']+'</td><td>'+str(round(float(category['spent'])))+'</td><td>'+str(round(float(category['earned'])))+'</td><td>'+str(round(float(category['total'])))+'</td></tr>'
			tableBody += '<tr><td>'+category['name']+'</td><td>'+str(round(float(category['total']))).replace("-", "−")+'</td></tr>'
		tableBody += '</table>'
		htmlBody = """
		<html>
			<head>
				<style>table{{border-collapse: collapse; border-top: 1px solid black; border-bottom: 1px solid black;}} th {{border-bottom: 1px solid black; padding: 0.33em 1em 0.33em 1em;}} td{{padding: .1em;}} tr:nth-child(even) {{background: #EEE}} tr:nth-child(odd) {{background: #FFF}} tr td:first-child {{padding-right: 1em;}} tr td:last-child, tr th:last-child {{text-align: right;}}</style>
			</head>
			<body>
				<p>Monthly categories report for {start} to {end}:</p>
				{tableBody}
			</body>
		</html>
		""".format( start=startDate.strftime('%Y-%m-%d'), end=endDate.strftime('%Y-%m-%d'), tableBody=tableBody )
		msg.set_content(BeautifulSoup(htmlBody).get_text()) # just html to text
		msg.add_alternative(htmlBody, subtype='html')
		#
		# Send off the message
		with smtplib.SMTP(config['smtp']['server']) as s:
			s.send_message(msg)

if __name__ == "__main__":
	main()
