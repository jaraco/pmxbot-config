"""
"""

import getpass

from fabric.contrib import files
from fabric import api
from fabric.api import sudo, run

@api.task
def install_config():
	irc_pass = getpass.getpass('Password for irc [skip]> ')
	db_pass = getpass.getpass('MongoDB password for pmxbot [skip]> ')
	twilio_token = getpass.getpass('Token for twilio [skip]> ')
	google_trans_key = getpass.getpass('Google Translate key [skip]> ')
	sudo('mkdir -p /etc/pmxbot')
	files.upload_template('pmxbot.conf', '/etc/pmxbot/main.conf',
		use_sudo=True)
	if irc_pass:
		files.upload_template('password.conf', '/etc/pmxbot/password.conf',
			context=dict(password=irc_pass), use_sudo=True, mode=0o600)
	if db_pass or not files.exists('/etc/pmxbot/database.conf'):
		files.upload_template('database.conf', '/etc/pmxbot/database.conf',
			context=dict(password=db_pass), use_sudo=True, mode=0o600)
	if twilio_token or not files.exists('/etc/pmxbot/twilio.conf'):
		files.upload_template('twilio.conf', '/etc/pmxbot/twilio.conf',
			context=dict(token=twilio_token), use_sudo=True, mode=0o600)
	if google_trans_key or not files.exists('/etc/pmxbot/trans.conf'):
		files.upload_template('trans.conf', '/etc/pmxbot/trans.conf',
			context=dict(key=google_trans_key), use_sudo=True, mode=0o600)

@api.task
def install_web_component():
	files.upload_template('web.conf', '/etc/pmxbot/web.conf',
		use_sudo=True)
	files.upload_template('supervisor web.conf',
		'/etc/supervisor/conf.d/pmxbotweb.conf', use_sudo=True)
	sudo('supervisorctl reload')

@api.task
def install_python():
	sudo('aptitude update')
	sudo('aptitude install -y python3.4')

@api.task
def install_setuptools():
	sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | python3.4')
	sudo('rm setuptools*')

packages = ' '.join([
	'pmxbot',
	'excuses',
	'popquotes',
	'pmxbot-wolframalpha',
	'jaraco.pmxbot',
	'pymongo',
	'chucknorris',
	'pmxbot-haiku',
	'twilio',
	'motivation',
	'jaraco.translate',
])

@api.task
def install_pmxbot():
	"Install pmxbot into a PEP-370 env at /usr/local/pmxbot"
	sudo('mkdir -p /usr/local/pmxbot/lib/python3.4/site-packages')
	sudo('PYTHONUSERBASE=/usr/local/pmxbot easy_install-3.4 --user '
		+ packages)

@api.task
def install_supervisor():
	sudo('aptitude install -y supervisor')
	files.upload_template('supervisor.conf',
		'/etc/supervisor/conf.d/pmxbot.conf', use_sudo=True)
	sudo('supervisorctl reload')

@api.task
def update_pmxbot():
	sudo('PYTHONUSERBASE=/usr/local/pmxbot easy_install-3.4 --user -U '
		+ packages)
	sudo('supervisorctl restart pmxbot')
	#sudo('supervisorctl restart pmxbotweb')

@api.task
def ensure_fqdn():
	"""
	Ensure 'hostname -f' returns a fully-qualified hostname.
	"""
	hostname = run('hostname -f')
	if '.' in hostname:
		return
	cmd = 'sed -i -e "s/{hostname}/{hostname}.dcpython.org {hostname}/g" /etc/hosts'
	cmd = cmd.format(hostname=hostname)
	sudo(cmd)

@api.task
def bootstrap():
	ensure_fqdn()
	install_config()
	install_python()
	install_setuptools()
	install_supervisor()
	install_pmxbot()
