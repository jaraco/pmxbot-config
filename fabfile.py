import getpass

from fabric.contrib import files
from fabric import api

@api.task
def install_config():
	context = dict(
		password=getpass.getpass('MongoDB password for pmxbot> '),
	)
	api.sudo('mkdir -p /etc/pmxbot')
	files.upload_template('database.conf', '/etc/pmxbot/database.conf',
		context=context, use_sudo=True, mode=0600)
	files.upload_template('pmxbot.conf', '/etc/pmxbot/main.conf',
		use_sudo=True)
