###############
# run-mc-server.py
# -------------
# Script for running a minecraft server with auto-update functionality.
# Tested on Windows and Ubuntu but *should* work on other OS's (Mac). 
# For Python 3.x.
#
# ---------
# Changelog
# ---------
script_version = '0.3'
# 0.3   - Added support for mac/linux
#       - Added configurable ram allocation for the server
#       - Fixed crash if you try to stop server before it's started
# 0.2.5 - Added configurable wait time
#       - Added setting window title
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
# ------
# server_type can be either 'snapshot' or 'release'
server_type = 'snapshot'
# wait_time is the time to wait until checking for an update (in minutes)
wait_time = 60
# ram_alloc is the amount of ram (in MB) to allocate to the server
ram_alloc = 2048
########################

server = ''
version_updated = False
server_stopped = True

# Send output to console
def m(message):
	print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] [r-mc-s.py - ' + script_version + ']: ' + message)

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
		if not server_stopped:
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
		if os.name is 'nt':
			# we are running under windows
			server = subprocess.Popen('start /I /B java -Xmx' + str(ram_alloc) + 'm -Xms' + str(ram_alloc) + 'm -jar server.jar nogui', stdin=subprocess.PIPE, shell=True)
		elif os.name is 'posix':
			# we are running under mac/linux
			server = subprocess.Popen('java -Xmx' + str(ram_alloc) + 'm -Xms' + str(ram_alloc) + 'm -jar server.jar nogui', stdin=subprocess.PIPE, shell=True)
		else:
			m('Unable to detect which OS you are running, exiting...')
			sys.exit(0)
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

# -------------------
# Main execution loop
# -------------------
# set window title
if os.name is 'nt':
	os.system('title ' + '[r-mc-s.py - ' + script_version + ']')
elif os.name is 'posix':
	sys.stdout.write('\x1b]2;[r-mc-s.py - ' + script_version + ']\x07')

m('Starting exectution...')

while True:
	try:
		version_check()
		update_server()
		start_server()
		m('Going to sleep for ' + str(wait_time) + ' minutes...')
		time.sleep(wait_time * 60) # wait time
		m('Waking up to check for updates...')

	except KeyboardInterrupt:
		stop_server(True)
		m('Exiting...')
		sys.exit(0)