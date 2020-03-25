"""
Install pmxbot on Bionic server
"""

import keyring
from fabric.contrib import files
from fabric import api
from fabric.api import sudo, run, env

domain = 'jaraco.com'
env.hosts = env.hosts or ['spidey']

python = 'python3.8'


@api.task
def install_config():
    slack_token = keyring.get_password('familyfortress.slack.com', 'pmxbot')
    db_pass = keyring.get_password(
        'mongodb.jaraco.com/family_fortress', 'pmxbot')
    twilio_token = keyring.get_password('Twilio', 'jaraco') or ''
    google_trans_key = keyring.get_password(
        'api.google.com/freenode', 'pmxbot')
    wolframalpha_key = keyring.get_password(
        'https://api.wolframalpha.com/', 'jaraco')
    sudo('mkdir -p /etc/pmxbot')
    files.upload_template(
        'pmxbot.conf', '/etc/pmxbot/main.conf',
        use_sudo=True)
    files.upload_template(
        'web.conf', '/etc/pmxbot/web.conf',
        use_sudo=True)
    if slack_token or not files.exists('/etc/pmxbot/server.conf'):
        files.upload_template(
            'server.conf', '/etc/pmxbot/server.conf',
            context={'slack token': slack_token}, use_sudo=True, mode=0o600)
    if db_pass or not files.exists('/etc/pmxbot/database.conf'):
        files.upload_template(
            'database.conf', '/etc/pmxbot/database.conf',
            context=dict(password=db_pass), use_sudo=True, mode=0o600)
    if twilio_token or not files.exists('/etc/pmxbot/twilio.conf'):
        files.upload_template(
            'twilio.conf', '/etc/pmxbot/twilio.conf',
            context=dict(token=twilio_token), use_sudo=True, mode=0o600)
    if google_trans_key or not files.exists('/etc/pmxbot/trans.conf'):
        files.upload_template(
            'trans.conf', '/etc/pmxbot/trans.conf',
            context=dict(key=google_trans_key), use_sudo=True, mode=0o600)
    if wolframalpha_key or not files.exists('/etc/pmxbot/wolframalpha.conf'):
        files.upload_template(
            'wolframalpha.conf', '/etc/pmxbot/wolframalpha.conf',
            context=dict(key=wolframalpha_key), use_sudo=True, mode=0o600)


@api.task
def install_python():
    sudo('apt-add-repository -y ppa:deadsnakes/ppa')
    sudo('apt update')
    sudo(f'apt -q install -y {python}-venv')


packages = ' '.join([
    'pmxbot[slack,mongodb]',
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

install_root = '/opt/pmxbot'


@api.task
def install_env():
    user = run('whoami')
    sudo(f'rm -R {install_root} || echo -n')
    sudo(f'mkdir -p {install_root}')
    sudo(f'chown {user} {install_root}')
    run(f'{python} -m venv {install_root}')
    run(f'{install_root}/bin/python -m pip install -U pip')


@api.task
def install_pmxbot():
    "Install pmxbot into a venv at install_root"
    run(f'{install_root}/bin/python -m pip install --upgrade '
        f'--upgrade-strategy=eager {packages}')


@api.task
def install_systemd_service():
    files.upload_template(
        'pmxbot.service',
        '/etc/systemd/system',
        context=globals(),
        use_sudo=True,
    )
    sudo('systemctl restart pmxbot')
    sudo('systemctl enable pmxbot')


@api.task
def install_systemd_web_service():
    files.upload_template(
        'web.conf', '/etc/pmxbot/web.conf',
        use_sudo=True)
    files.upload_template(
        'pmxbot.web.service',
        '/etc/systemd/system',
        context=globals(),
        use_sudo=True,
    )
    sudo('systemctl restart pmxbot.web')
    sudo('systemctl enable pmxbot.web')


@api.task
def update_pmxbot():
    install_pmxbot()
    sudo('systemctl restart pmxbot')


@api.task
def ensure_fqdn():
    """
    Ensure 'hostname -f' returns a fully-qualified hostname.
    """
    hostname = run('hostname -f')
    if '.' in hostname:
        return
    sudo(
        f'sed -i -e "s/{hostname}/{hostname}.{domain} {hostname}/g" /etc/hosts'
    )
    assert '.' in run('hostname -f')


@api.task
def bootstrap():
    ensure_fqdn()
    install_config()
    install_python()
    install_env()
    install_pmxbot()
    install_systemd_service()
