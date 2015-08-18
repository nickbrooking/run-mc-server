###############
# run-mc-server.py
# -------------
# Script for running a minecraft server with auto-update functionality.
# Tested on Windows but *should* work on other OS's with slight tweaks. 
# For Python 3.x.
#
# ---------
# Changelog
# ---------
script_version = '0.2.4'
# 0.2.4 - Added outputting current time on messages
# 0.2.3 - Server won't start unless it's stopped
#       - Refactored a bit to simplify the code
# 0.2.2 - Server won't stop unless update needed
# 0.2.1 - Removed some things that weren't needed
# 0.2   - Added checking to see if server already up to date
#       - Added better handling for stopping the server manually
# 0.1   - Initial release
# -------------
# Nick Brooking
###############

import datetime
import filecmp
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

########
# Config
# server_type can be either 'snapshot' or 'release'
server_type = 'snapshot'
########################

server = ''
version_updated = False
server_stopped = True

# Send output to console
def m(message):
	print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] [rs.py - ' + script_version + ']: ' + message)

# Send command to server
def c(command):
	global server

	server.stdin.write((command + '\n').encode())
	server.stdin.flush()

def version_check():
	global version_updated

	m('Checking to see if update is needed...')
	urllib.request.urlretrieve('https://s3.amazonaws.com/Minecraft.Download/versions/versions.json', 'versions_new.json');
	if not os.path.exists('versions.json') or not filecmp.cmp('versions_new.json','versions.json'):
		version_updated = True
	else:
		version_updated = False

def update_server():
	if version_updated:
		stop_server(False)
		m('Updating server.jar, please wait...')
		shutil.copy2('versions_new.json','versions.json')

		with open('versions.json') as versions_file:
			versions = json.load(versions_file)

		if server_type == 'snapshot':
			version = versions["latest"]["snapshot"]
		else:
			version = versions["latest"]["release"]

		urllib.request.urlretrieve('https://s3.amazonaws.com/Minecraft.Download/versions/' + version + '/minecraft_server.' + version + '.jar', 'server.jar');
	else:
		m('Server already up to date. No update needed.')

def start_server():
	global server
	global server_stopped
	
	if server_stopped:
		m('Starting server...')
		server = subprocess.Popen('start /I /B java -Xmx2048m -Xms2048m -jar server.jar nogui', stdin=subprocess.PIPE, shell=True)
		server_stopped = False

def stop_server(now):
	global server
	global server_stopped

	m('Server stopping...')

	if now:
		c('stop')
		time.sleep(10)
		server.kill()
		server_stopped = True
	else:
		c('say The server is going down for update in 5 minutes!')
		time.sleep(240) # wait 4 minutes
		c('say The server is going down for update in 1 minute!')
		time.sleep(5) # wait a few seconds in between messages
		c('say The server will be back up shortly.')
		time.sleep(60) # wait one minute
		c('stop')
		time.sleep(10)
		server.kill()
		server_stopped = True

	time.sleep(10) # wait 10 more seconds to let things cool down

# Main execution loop
m('Starting exectution...')
while True:
	try:
		version_check()
		update_server()
		start_server()
		m('Going to sleep for one hour...')
		time.sleep(3600) # wait 1 hour
		m('Waking up to check for updates...')

	except KeyboardInterrupt:
		stop_server(True)
		m('Exiting...')
		sys.exit(0)