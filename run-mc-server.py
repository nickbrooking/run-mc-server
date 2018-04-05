##################
# run-mc-server.py
# -------------
# Script for running a minecraft server with auto-update functionality.
# Tested on Windows and Ubuntu but *should* work on other OS's (Mac). 
# For Python 3.x.
#
# ---------
# Changelog
# ---------
script_version = '0.3.2'
# 0.3.2 - Moved backup to before getting new version
# 0.3.1 - Added backing up world before updating
#       - Added checking to see if server.jar still exists
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
import zipfile

########
# Config
# ------
# server_type can be either 'snapshot' or 'release'
server_type = 'snapshot'
# wait_time is the time to wait until checking for an update (in minutes)
wait_time = 60
# ram_alloc is the amount of ram (in MB) to allocate to the server
ram_alloc = 2048
# backups is whether or not you want backups
backups = True
# backup_at_wait_time is if you want a backup to be created every 'wait_time'
# Set to false by default as it could really fill your hard drive if you set your wait_time too low
backup_at_wait_time = False
# world_name is the name of your world, for backup purposes
world_name = 'world'
# backups_dir is the name of your backups folder
backups_dir = 'backups'
#######################

##################
# Global Variables
# ----------------
server = ''
version = ''
version_updated = False
server_stopped = True
#####################

##################
# Helper Functions
# ----------------
# Send output to console
def m(message):
	print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] [r-mc-s.py - ' + script_version + ']: ' + message)

# Send command to server
def c(command):
	global server

	server.stdin.write((command + '\n').encode())
	server.stdin.flush()

def zipdir(path, ziph):
	for root, dirs, files in os.walk(world_name):
		for file in files:
			ziph.write(os.path.join(root, file))

def get_mc_version():
	global version

	with open('versions.json') as versions_file:
		versions = json.load(versions_file)

	if server_type == 'snapshot':
		version = versions["latest"]["snapshot"]
	else:
		version = versions["latest"]["release"]
###############################################

################
# Main Functions
# --------------
def version_check():
	global version_updated

	m('Checking to see if update is needed...')
	urllib.request.urlretrieve('https://launchermeta.mojang.com/mc/game/version_manifest.json', 'versions_new.json');
	if not os.path.exists('versions.json') or not os.path.exists('server.jar') or not filecmp.cmp('versions_new.json','versions.json'):
		update_server()
	else:
		get_mc_version() # get current version here just so we have it
		m('Server already up to date. No update needed.')

def backup_world():
	if not server_stopped:
		c('say Backing up world.')

	m('Creating a backup of the world...')
	try:
		if not os.path.exists(backups_dir):
			os.makedirs(backups_dir)
		zipf = zipfile.ZipFile(backups_dir + '/' + world_name + '_' + version + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.zip', 'w')
		zipdir(world_name + '/', zipf)
		zipf.close()
		m('Backup created.')
	except:
		m('Unable to create backup.')

def update_server():
	global version

	if not server_stopped:
		stop_server(False)
	m('Updating server.jar, please wait...')
	shutil.copy2('versions_new.json','versions.json')
	
	# Create a backup of the world before we go on and start the new server
	if backups:
		backup_world()

	# get the version from the new json file
	get_mc_version()

	urllib.request.urlretrieve('https://s3.amazonaws.com/Minecraft.Download/versions/' + version + '/minecraft_server.' + version + '.jar', 'server.jar');

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
##################

#####################
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
		start_server()
		m('Going to sleep for ' + str(wait_time) + ' minutes...')
		time.sleep(wait_time * 60) # wait time
		m('Waking up to check for updates...')
		if backups and backup_at_wait_time:
			backup_world()

	except KeyboardInterrupt:
		stop_server(True)
		m('Exiting...')
		sys.exit(0)
###################
