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
