"""
Install pmxbot on DCPython's Saucy Salamander server
"""

import getpass

from fabric.contrib import files
from fabric.context_managers import shell_env
from fabric import api
from fabric.api import sudo, run, env

env.hosts = ['chat-logs.dcpython.org']

python = 'python3.4'

@api.task
def install_config():
	db_pass = getpass.getpass('MongoDB password for pmxbot [skip]> ')
	twilio_token = getpass.getpass('Token for twilio [skip]> ')
	google_trans_key = getpass.getpass('Google Translate key [skip]> ')
	wolframalpha_key = getpass.getpass('Wolfram|Alpha key [skip]> ')
	sudo('mkdir -p /etc/pmxbot')
	files.upload_template('pmxbot.conf', '/etc/pmxbot/main.conf',
		use_sudo=True)
	files.upload_template('web.conf', '/etc/pmxbot/web.conf',
		use_sudo=True)
	if db_pass:
		files.upload_template('database.conf', '/etc/pmxbot/database.conf',
			context=dict(password=db_pass), use_sudo=True, mode=0o600)
	if twilio_token or not files.exists('/etc/pmxbot/twilio.conf'):
		files.upload_template('twilio.conf', '/etc/pmxbot/twilio.conf',
			context=dict(token=twilio_token), use_sudo=True, mode=0o600)
	if google_trans_key or not files.exists('/etc/pmxbot/trans.conf'):
		files.upload_template('trans.conf', '/etc/pmxbot/trans.conf',
			context=dict(key=google_trans_key), use_sudo=True, mode=0o600)
	if wolframalpha_key or not files.exists('/etc/pmxbot/wolframalpha.conf'):
		files.upload_template('wolframalpha.conf', '/etc/pmxbot/wolframalpha.conf',
			context=dict(key=wolframalpha_key), use_sudo=True, mode=0o600)

@api.task
def install_python():
	sudo('aptitude install -y software-properties-common')
	sudo('apt-add-repository -y ppa:fkrull/deadsnakes')
	sudo('aptitude update')
	sudo('aptitude install -y {python}'.format_map(globals()))

@api.task
def install_setuptools():
	tmpl = 'wget https://bootstrap.pypa.io/ez_setup.py -O - | {python}'
	sudo(tmpl.format_map(globals()))
	sudo('rm setuptools*')

packages = ' '.join([
	'pmxbot',
	'excuses',
	'popquotes',
	'wolframalpha',
	'jaraco.pmxbot',
	'pymongo',
	'chucknorris',
	'pmxbot-haiku',
	'twilio',
	'motivation',
	'jaraco.translate',
])

install_env = dict(
	PYTHONUSERBASE='/usr/local/pmxbot',
)

@api.task
def install_pmxbot():
	"Install pmxbot into a PEP-370 env at /usr/local/pmxbot"
	tmpl = 'mkdir -p /usr/local/pmxbot/lib/{python}/site-packages'
	sudo(tmpl.formap_map(globals()))
	tmpl = '{python} -m easy_install --user {packages}'
	with shell_env(**install_env):
		sudo(tmpl.format_map(globals()))

@api.task
def install_supervisor():
	sudo('aptitude install -y supervisor')
	files.upload_template('supervisor.conf',
		'/etc/supervisor/conf.d/pmxbot.conf', use_sudo=True)
	sudo('supervisorctl reload')

@api.task
def update_pmxbot():
	tmpl = '{python} -m easy_install --user -U {packages}'
	with shell_env(**install_env):
		sudo(tmpl.format_map(globals()))
	sudo('supervisorctl restart pmxbot')
	sudo('supervisorctl restart pmxbotweb')

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
