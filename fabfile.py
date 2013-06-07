import getpass

from fabric.contrib import files
from fabric import api
from fabric.api import sudo, run, cd

@api.task
def install_config():
	context = dict(
		password=getpass.getpass('MongoDB password for pmxbot> '),
	)
	sudo('mkdir -p /etc/pmxbot')
	files.upload_template('database.conf', '/etc/pmxbot/database.conf',
		context=context, use_sudo=True, mode=0600)
	files.upload_template('pmxbot.conf', '/etc/pmxbot/main.conf',
		use_sudo=True)

@api.task
def install_python(version='3.3.2'):
	sudo('aptitude update')
	sudo('aptitude build-dep -y python')
	sudo('aptitude install -y libssl-dev libsqlite3-dev libreadline-dev libbz2-dev')
	url = ('http://www.python.org'
		'/ftp/python/{version}/Python-{version}.tgz').format(**vars())
	run('wget {url} -O - | tar xz'.format(url=url))
	with cd('Python-{version}'.format(**vars())):
		run('./configure')
		run('make')
		sudo('make install')
	sudo('rm -Rf Python-{version}'.format(**vars()))

@api.task
def install_setuptools():
	sudo('wget https://bitbucket.org/pypa/setuptools/raw/0.7.1/ez_setup.py -O - | python3.3')
	sudo('rm setuptools*')

packages = ' '.join([
	'pmxbot',
	'pmxbot-wolframalpha',
	'jaraco.pmxbot',
	'pymongo',
	'chucknorris',
	'pmxbot-haiku',
])

@api.task
def install_pmxbot():
	"Install pmxbot into a PEP-370 env at /usr/local/pmxbot"
	sudo('mkdir -p /usr/local/pmxbot/lib/python3.3/site-packages')
	sudo('PYTHONUSERBASE=/usr/local/pmxbot easy_install-3.3 --user '
		+ packages)

@api.task
def install_supervisor():
	sudo('aptitude install -y supervisor')
	files.upload_template('supervisor.conf',
		'/etc/supervisor/conf.d/pmxbot.conf')
	sudo('supervisorctl reload')

@api.task
def update_pmxbot():
	sudo('PYTHONUSERBASE=/usr/local/pmxbot easy_install-3.3 --user -U '
		+ packages)
	sudo('supervisorctl restart pmxbot')
	sudo('supervisorctl restart pmxbotweb')

@api.task
def bootstrap():
	install_config()
	install_python()
	install_setuptools()
	install_supervisor()
	install_pmxbot()
