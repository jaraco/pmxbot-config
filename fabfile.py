"""
"""

import getpass

from fabric.contrib import files
from fabric.context_managers import shell_env
from fabric import api
from fabric.api import sudo, run, env

env.hosts = ['punisher']
domain = 'jaraco.com'

@api.task
def install_config():
	irc_pass = getpass.getpass('Password for irc [skip]> ')
	db_pass = getpass.getpass('MongoDB password for pmxbot [skip]> ')
	twilio_token = getpass.getpass('Token for twilio [skip]> ')
	google_trans_key = getpass.getpass('Google Translate key [skip]> ')
	wolframalpha_key = getpass.getpass('Wolfram|Alpha key [skip]> ')
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
	if wolframalpha_key or not files.exists('/etc/pmxbot/wolframalpha.conf'):
		files.upload_template('wolframalpha.conf', '/etc/pmxbot/wolframalpha.conf',
			context=dict(key=wolframalpha_key), use_sudo=True, mode=0o600)

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
	sudo('aptitude -q install -y python3-pip')

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
	tmpl = 'python3 -m pip install --user {packages}'
	with shell_env(**install_env):
		usp = run('python3 -c "import site; print(site.getusersitepackages())"')
		sudo("mkdir -p {usp}".format(**locals()))
		sudo(tmpl.format_map(globals()))

@api.task
def install_supervisor():
	sudo('aptitude -q install -y supervisor')
	files.upload_template('supervisor.conf',
		'/etc/supervisor/conf.d/pmxbot.conf', use_sudo=True)
	sudo('supervisorctl reload')

@api.task
def update_pmxbot():
	tmpl = 'python3 -m pip install --user -U {packages}'
	with shell_env(**install_env):
		sudo(tmpl.format_map(globals()))
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
	cmd = 'sed -i -e "s/{hostname}/{hostname}.{domain} {hostname}/g" /etc/hosts'
	cmd = cmd.format(hostname=hostname, domain=domain)
	sudo(cmd)

@api.task
def bootstrap():
	ensure_fqdn()
	install_config()
	install_python()
	install_supervisor()
	install_pmxbot()
