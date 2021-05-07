from io import BytesIO
from getpass import getuser
from secrets import token_urlsafe
from socket import gethostname
from socket import gethostbyname_ex
from typing import Dict
from uuid import uuid4
import logging

from jinja2 import Template
import click
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

from dallinger.command_line.config import get_configured_hosts
from dallinger.command_line.config import remove_host
from dallinger.command_line.config import store_host
from dallinger.config import get_config
from dallinger.utils import abspath_from_egg


# Find an identifier for the current user to use as CREATOR of the experiment
HOSTNAME = gethostname()
try:
    USER = getuser()
except KeyError:
    USER = "user"

DOCKER_COMPOSE_SERVER = abspath_from_egg(
    "dallinger", "dallinger/docker/ssh_templates/docker-compose-server.yml"
).read_bytes()

DOCKER_COMPOSE_EXP_TPL = Template(
    abspath_from_egg(
        "dallinger", "dallinger/docker/ssh_templates/docker-compose-experiment.yml.j2"
    ).read_text()
)


CADDYFILE = """
# This is a configuration file for the Caddy http Server
# Documentation can be found at https://caddyserver.com/docs
{host} {{
    respond /health-check 200
    {tls}
}}

import caddy.d/*
"""


@click.group()
@click.pass_context
def docker_ssh(ctx):
    """Deploy to a remote server using docker through ssh."""


@docker_ssh.group()
def servers():
    """Manage remote servers where experiments can be deployed"""


@servers.command(name="list")
def list_servers():
    hosts = get_configured_hosts()
    if not hosts:
        print("No server configured. Use `dallinger docker-ssh servers add` to add one")
    for host in hosts.values():
        print(", ".join(f"{key}: {value}" for key, value in host.items()))


@servers.command()
@click.option(
    "--host", required=True, help="IP address or dns name of the remote server"
)
@click.option("--user", help="User to use when connecting to remote host")
def add(host, user):
    """Add a server to deploy experiments through ssh using docker.
    The server needs docker and docker-compose usable by the current user.
    Port 80 and 443 must be free for dallinger to use.
    In case docker and/or docker-compose are missing, dallnger will try to
    install them using `sudo`. The given user must have passwordless sudo rights.
    """
    prepare_server(host, user)
    store_host(dict(host=host, user=user))


@servers.command()
@click.option(
    "--host", required=True, help="IP address or dns name of the remote server"
)
def remove(host):
    """Remove server from list of known remote servers.
    No action is performed remotely.
    """
    remove_host(host)


def prepare_server(host, user):
    executor = Executor(host, user)
    print("Checking docker presence")
    try:
        executor.run("docker ps")
    except ExecuteException:
        print("Installing docker")
        executor.run("wget -O - https://get.docker.com | bash")
        executor.run(f"sudo adduser {user} docker")
        print("Docker installed")
        # Log in again in case we need to be part of the `docker` group
        executor = Executor(host, user)
    else:
        print("Docker daemon already installed")

    try:
        executor.run("docker-compose --version")
    except ExecuteException:
        try:
            install_docker_compose_via_pip(executor)
        except ExecuteException:
            executor.run(
                "sudo wget https://github.com/docker/compose/releases/download/1.29.1/docker-compose-Linux-x86_64 -O /usr/local/bin/docker-compose"
            )
            executor.run("sudo chmod 755 /usr/local/bin/docker-compose")
    else:
        print("Docker compose already installed")


def install_docker_compose_via_pip(executor):
    try:
        executor.run("python3 --version")
    except ExecuteException:
        # No python: better give up
        return

    try:
        executor.run("python3 -m pip --version")
    except ExecuteException:
        # No pip. Let's try to install it
        executor.run("python3 <(wget -O - https://bootstrap.pypa.io/get-pip.py)")
    executor.run("python3 -m pip install --user docker-compose")
    executor.run("sudo ln -s ~/.local/bin/docker-compose /usr/local/bin/docker-compose")
    print("docker-compose installed using pip")


server_option = click.option(
    "--server",
    required=True,
    help="Server to deploy to",
    prompt="Choose one of the configured servers (add one with `dallinger docker-ssh servers add`)\n",
    type=click.Choice(tuple(get_configured_hosts().keys())),
)


@docker_ssh.command()
@click.option(
    "--sandbox",
    "mode",
    flag_value="sandbox",
    help="Deploy to MTurk sandbox",
    default=True,
)
@click.option("--live", "mode", flag_value="live", help="Deploy to the real MTurk")
@click.option("--image", required=True, help="Name of the docker image to deploy")
@server_option
@click.option(
    "--dns-host",
    help="DNS name to use. Must resolve all its subdomains to the IP address specified as ssh host",
)
@click.option("--config", "-c", "config_options", nargs=2, multiple=True)
def deploy(mode, image, server, dns_host, config_options):
    server_info = get_configured_hosts()[server]
    ssh_host = server_info["host"]
    ssh_user = server_info.get("user")
    HAS_TLS = ssh_host != "localhost"
    tls = "tls internal" if not HAS_TLS else ""
    if not dns_host:
        dns_host = get_dns_host(ssh_host)
    executor = Executor(ssh_host, user=ssh_user)
    executor.run("mkdir -p ~/dallinger/caddy.d")

    sftp = get_sftp(ssh_host, user=ssh_user)
    sftp.putfo(BytesIO(DOCKER_COMPOSE_SERVER), "dallinger/docker-compose.yml")
    sftp.putfo(
        BytesIO(CADDYFILE.format(host=dns_host, tls=tls).encode()),
        "~/dallinger/Caddyfile",
    )
    executor.run("docker-compose -f ~/dallinger/docker-compose.yml up -d")
    print("Launched http and postgresql servers. Starting experiment")

    experiment_uuid = str(uuid4())
    experiment_id = f"dlgr-{experiment_uuid[:8]}"
    dashboard_password = token_urlsafe(8)
    config = get_config()
    config.load()
    cfg = config.as_dict()
    cfg.update(
        {
            "FLASK_SECRET_KEY": token_urlsafe(16),
            "dashboard_password": dashboard_password,
            "mode": mode,
            "CREATOR": f"{USER}@{HOSTNAME}",
            "DALLINGER_UID": experiment_uuid,
            "ADMIN_USER": "admin",
        }
    )
    cfg.update(config_options)
    del cfg["host"]  # The uppercase variable will be used instead
    executor.run(f"mkdir -p dallinger/{experiment_id}")
    sftp.putfo(
        BytesIO(get_docker_compose_yml(cfg, experiment_id, image).encode()),
        f"dallinger/{experiment_id}/docker-compose.yml",
    )
    executor.run(
        f"docker-compose -f ~/dallinger/{experiment_id}/docker-compose.yml up -d"
    )
    print(f"Experiment {experiment_id} started. Initializing database")
    executor.run(
        f"docker-compose -f ~/dallinger/{experiment_id}/docker-compose.yml exec -T web dallinger-housekeeper initdb"
    )
    print("Database initialized")

    caddy_conf = f"{experiment_id}.{dns_host} {{\n    {tls}\n    reverse_proxy {experiment_id}_web:5000\n}}"
    sftp.putfo(
        BytesIO(caddy_conf.encode()),
        f"~/dallinger/caddy.d/{experiment_id}",
    )
    # Tell caddy we changed something in the configuration
    executor.reload_caddy()

    print("Launching experiment")
    response = get_retrying_http_client().post(
        f"https://{experiment_id}.{dns_host}/launch", verify=HAS_TLS
    )
    print(response.json()["recruitment_msg"])

    print("To display the logs for this experiment you can run:")
    print(
        f"ssh {ssh_user}@{ssh_host} docker-compose -f '~/dallinger/{experiment_id}/docker-compose.yml' logs -f"
    )
    print(
        f"You can now log in to the console at https://{experiment_id}.{dns_host}/dashboard as user {cfg['ADMIN_USER']} using password {cfg['dashboard_password']}"
    )


@docker_ssh.command()
@server_option
def apps(server):
    """List dallinger apps running on the remote server."""
    server_info = get_configured_hosts()[server]
    ssh_host = server_info["host"]
    ssh_user = server_info.get("user")
    executor = Executor(ssh_host, user=ssh_user)
    # The caddy configuration files are used as source of truth
    # to get the list of installed apps
    apps = executor.run("ls ~/dallinger/caddy.d")
    for app in apps.split():
        print(app)


@docker_ssh.command()
@click.option("--app", required=True, help="Name of the experiment app to destroy")
@server_option
def destroy(server, app):
    """Tear down an experiment run on a server you control via ssh."""
    server_info = get_configured_hosts()[server]
    ssh_host = server_info["host"]
    ssh_user = server_info.get("user")
    executor = Executor(ssh_host, user=ssh_user)
    # Remove the caddy configuration file and reload caddy config
    try:
        executor.run(f"ls ~/dallinger/caddy.d/{app}")
    except ExecuteException:
        print(f"App {app} not found on server {server}")
        raise click.Abort
    executor.run(f"rm ~/dallinger/caddy.d/{app}")
    executor.reload_caddy()
    executor.run(
        f"docker-compose -f ~/dallinger/{app}/docker-compose.yml down", raise_=False
    )
    executor.run(f"rm -rf ~/dallinger/{app}/")
    print(f"App {app} removed")


def get_docker_compose_yml(
    config: Dict[str, str], experiment_id: str, experiment_image: str
) -> str:
    """Generate a docker-compose.yml file based on the given"""
    return DOCKER_COMPOSE_EXP_TPL.render(
        experiment_id=experiment_id, experiment_image=experiment_image, config=config
    )


def get_retrying_http_client():
    retry_strategy = Retry(
        total=10,
        backoff_factor=0.2,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http


def get_dns_host(ssh_host):
    ip_addr = gethostbyname_ex(ssh_host)[2][0]
    return f"{ip_addr}.nip.io"


class Executor:
    """Execute remote commands using paramiko"""

    def __init__(self, host, user=None):
        import paramiko

        self.client = paramiko.SSHClient()
        # For convenience we always trust the remote host
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        print(f"Connecting to {host}")
        self.client.connect(host, username=user)
        print("Connected.")

    def run(self, cmd, raise_=True):
        """Run the given command and block until it completes.
        If `raise` is True and the command fails, print the reason and raise an exception.
        """
        channel = self.client.get_transport().open_session()
        channel.exec_command(cmd)
        status = channel.recv_exit_status()
        if raise_ and status != 0:
            print(f"Error: exit code was not 0 ({status})")
            print(channel.recv(10 ** 10).decode())
            print(channel.recv_stderr(10 ** 10).decode())
            raise ExecuteException
        return channel.recv(10 ** 10).decode()

    def reload_caddy(self):
        self.run(
            "docker-compose -f ~/dallinger/docker-compose.yml exec -T httpserver "
            "caddy reload -config /etc/caddy/Caddyfile"
        )


class ExecuteException(Exception):
    pass


def get_sftp(host, user=None):
    import paramiko

    client = paramiko.SSHClient()
    # For convenience we always trust the remote host
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(host, username=user)
    return client.open_sftp()


logger = logging.getLogger("paramiko.transport")
logger.setLevel(logging.ERROR)
