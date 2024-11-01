# imports - standard imports
import contextlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from glob import glob
from json.decoder import JSONDecodeError
from pathlib import Path

# imports - third party imports
import click

# imports - module imports
import wrench
from wrench.exceptions import PatchError, ValidationError
from wrench.utils import (
	exec_cmd,
	get_wrench_cache_path,
	get_wrench_name,
	get_cmd_output,
	log,
	which,
)

logger = logging.getLogger(wrench.PROJECT_NAME)


@lru_cache(maxsize=None)
def get_env_cmd(cmd: str, wrench_path: str = ".") -> str:
	exact_location = os.path.abspath(
		os.path.join(wrench_path, "env", "bin", cmd.strip("*"))
	)
	if os.path.exists(exact_location):
		return exact_location

	# this supports envs' generated by patched virtualenv or venv (which may cause an extra 'local' folder to be created)
	existing_python_bins = glob(
		os.path.join(wrench_path, "env", "**", "bin", cmd), recursive=True
	)

	if existing_python_bins:
		return os.path.abspath(existing_python_bins[0])

	return exact_location


def get_venv_path(verbose=False, python="python3"):
	with open(os.devnull, "wb") as devnull:
		is_venv_installed = not subprocess.call(
			[python, "-m", "venv", "--help"], stdout=devnull
		)
	if is_venv_installed:
		return f"{python} -m venv"
	else:
		log("venv cannot be found", level=2)


def update_node_packages(wrench_path=".", apps=None, verbose=None):
	print("Updating node packages...")
	from distutils.version import LooseVersion

	from wrench.utils.app import get_develop_version

	v = LooseVersion(get_develop_version("saashq", wrench_path=wrench_path))

	# After rollup was merged, saashq_version = 10.1
	# if develop_verion is 11 and up, only then install yarn
	if v < LooseVersion("11.x.x-develop"):
		update_npm_packages(wrench_path, apps=apps, verbose=verbose)
	else:
		update_yarn_packages(wrench_path, apps=apps, verbose=verbose)


def install_python_dev_dependencies(wrench_path=".", apps=None, verbose=False):
	import wrench.cli
	from wrench.wrench import Wrench

	verbose = wrench.cli.verbose or verbose
	quiet_flag = "" if verbose else "--quiet"

	wrench = Wrench(wrench_path)

	if isinstance(apps, str):
		apps = (apps,)
	elif not apps:
		apps = wrench.get_installed_apps()

	for app in apps:
		pyproject_deps = None
		app_path = os.path.join(wrench_path, "apps", app)
		pyproject_path = os.path.join(app_path, "pyproject.toml")
		dev_requirements_path = os.path.join(app_path, "dev-requirements.txt")

		if os.path.exists(pyproject_path):
			pyproject_deps = _generate_dev_deps_pattern(pyproject_path)
			if pyproject_deps:
				wrench.run(f"{wrench.python} -m pip install {quiet_flag} --upgrade {pyproject_deps}")

		if not pyproject_deps and os.path.exists(dev_requirements_path):
			wrench.run(
				f"{wrench.python} -m pip install {quiet_flag} --upgrade -r {dev_requirements_path}"
			)


def _generate_dev_deps_pattern(pyproject_path):
	try:
		from tomli import loads
	except ImportError:
		from tomllib import loads

	requirements_pattern = ""
	pyroject_config = loads(open(pyproject_path).read())

	with contextlib.suppress(KeyError):
		for pkg, version in pyroject_config["tool"]["wrench"]["dev-dependencies"].items():
			op = "==" if "=" not in version else ""
			requirements_pattern += f"{pkg}{op}{version} "
	return requirements_pattern


def update_yarn_packages(wrench_path=".", apps=None, verbose=None):
	import wrench.cli as wrench_cli
	from wrench.wrench import Wrench

	verbose = wrench_cli.verbose or verbose
	wrench = Wrench(wrench_path)
	apps = apps or wrench.apps
	apps_dir = os.path.join(wrench.name, "apps")

	# TODO: Check for stuff like this early on only??
	if not which("yarn"):
		print("Please install yarn using below command and try again.")
		print("`npm install -g yarn`")
		return

	for app in apps:
		app_path = os.path.join(apps_dir, app)
		if os.path.exists(os.path.join(app_path, "package.json")):
			click.secho(f"\nInstalling node dependencies for {app}", fg="yellow")
			yarn_install = "yarn install --check-files"
			if verbose:
				yarn_install += " --verbose"
			wrench.run(yarn_install, cwd=app_path)


def update_npm_packages(wrench_path=".", apps=None, verbose=None):
	verbose = wrench.cli.verbose or verbose
	npm_install = "npm install --verbose" if verbose else "npm install"
	apps_dir = os.path.join(wrench_path, "apps")
	package_json = {}

	if not apps:
		apps = os.listdir(apps_dir)

	for app in apps:
		package_json_path = os.path.join(apps_dir, app, "package.json")

		if os.path.exists(package_json_path):
			with open(package_json_path) as f:
				app_package_json = json.loads(f.read())
				# package.json is usually a dict in a dict
				for key, value in app_package_json.items():
					if key not in package_json:
						package_json[key] = value
					else:
						if isinstance(value, dict):
							package_json[key].update(value)
						elif isinstance(value, list):
							package_json[key].extend(value)
						else:
							package_json[key] = value

	if package_json == {}:
		with open(os.path.join(os.path.dirname(__file__), "package.json")) as f:
			package_json = json.loads(f.read())

	with open(os.path.join(wrench_path, "package.json"), "w") as f:
		f.write(json.dumps(package_json, indent=1, sort_keys=True))

	exec_cmd(npm_install, cwd=wrench_path)


def migrate_env(python, backup=False):
	import shutil
	from urllib.parse import urlparse

	from wrench.wrench import Wrench

	wrench = Wrench(".")
	nvenv = "env"
	path = os.getcwd()
	python = which(python)
	pvenv = os.path.join(path, nvenv)

	if python.startswith(pvenv):
		# The supplied python version is in active virtualenv which we are about to nuke.
		click.secho(
			"Python version supplied is present in currently sourced virtual environment.\n"
			"`deactiviate` the current virtual environment before migrating environments.",
			fg="yellow",
		)
		sys.exit(1)

	# Clear Cache before Wrench Dies.
	try:
		config = wrench.conf
		rredis = urlparse(config["redis_cache"])
		redis = f"{which('redis-cli')} -p {rredis.port}"

		logger.log("Clearing Redis Cache...")
		exec_cmd(f"{redis} FLUSHALL")
		logger.log("Clearing Redis DataBase...")
		exec_cmd(f"{redis} FLUSHDB")
	except Exception:
		logger.warning("Please ensure Redis Connections are running or Daemonized.")

	# Backup venv: restore using `virtualenv --relocatable` if needed
	if backup:
		from datetime import datetime

		parch = os.path.join(path, "archived", "envs")
		os.makedirs(parch, exist_ok=True)

		source = os.path.join(path, "env")
		target = parch

		logger.log("Backing up Virtual Environment")
		stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		dest = os.path.join(path, str(stamp))

		os.rename(source, dest)
		shutil.move(dest, target)

	# Create virtualenv using specified python
	def _install_app(app):
		app_path = f"-e {os.path.join('apps', app)}"
		exec_cmd(f"{pvenv}/bin/python -m pip install --upgrade {app_path}")

	try:
		logger.log(f"Setting up a New Virtual {python} Environment")
		exec_cmd(f"{python} -m venv {pvenv}")

		# Install saashq first
		_install_app("saashq")
		for app in wrench.apps:
			if str(app) != "saashq":
				_install_app(app)

		logger.log(f"Migration Successful to {python}")
	except Exception:
		logger.warning("Python env migration Error", exc_info=True)
		raise


def validate_upgrade(from_ver, to_ver, wrench_path="."):
	if to_ver >= 6 and not which("npm") and not which("node") and not which("nodejs"):
		raise Exception("Please install nodejs and npm")


def post_upgrade(from_ver, to_ver, wrench_path="."):
	from wrench.wrench import Wrench
	from wrench.config import redis
	from wrench.config.nginx import make_nginx_conf
	from wrench.config.supervisor import generate_supervisor_config

	conf = Wrench(wrench_path).conf
	print("-" * 80 + f"Your wrench was upgraded to version {to_ver}")

	if conf.get("restart_supervisor_on_update"):
		redis.generate_config(wrench_path=wrench_path)
		generate_supervisor_config(wrench_path=wrench_path)
		make_nginx_conf(wrench_path=wrench_path)
		print(
			"As you have setup your wrench for production, you will have to reload"
			" configuration for nginx and supervisor. To complete the migration, please"
			" run the following commands:\nsudo service nginx restart\nsudo"
			" supervisorctl reload"
		)


def patch_sites(wrench_path="."):
	from wrench.wrench import Wrench
	from wrench.utils.system import migrate_site

	wrench = Wrench(wrench_path)

	for site in wrench.sites:
		try:
			migrate_site(site, wrench_path=wrench_path)
		except subprocess.CalledProcessError:
			raise PatchError


def restart_supervisor_processes(wrench_path=".", web_workers=False, _raise=False):
	from wrench.wrench import Wrench

	wrench = Wrench(wrench_path)
	conf = wrench.conf
	cmd = conf.get("supervisor_restart_cmd")
	wrench_name = get_wrench_name(wrench_path)

	if cmd:
		wrench.run(cmd, _raise=_raise)

	else:
		sudo = ""
		try:
			supervisor_status = get_cmd_output("supervisorctl status", cwd=wrench_path)
		except subprocess.CalledProcessError as e:
			if e.returncode == 127:
				log("restart failed: Couldn't find supervisorctl in PATH", level=3)
				return
			sudo = "sudo "
			supervisor_status = get_cmd_output("sudo supervisorctl status", cwd=wrench_path)

		if not sudo and (
			"error: <class 'PermissionError'>, [Errno 13] Permission denied" in supervisor_status
		):
			sudo = "sudo "
			supervisor_status = get_cmd_output("sudo supervisorctl status", cwd=wrench_path)

		if web_workers and f"{wrench_name}-web:" in supervisor_status:
			groups = [f"{wrench_name}-web:\t"]

		elif f"{wrench_name}-workers:" in supervisor_status:
			groups = [f"{wrench_name}-web:", f"{wrench_name}-workers:"]

		# backward compatibility
		elif f"{wrench_name}-processes:" in supervisor_status:
			groups = [f"{wrench_name}-processes:"]

		# backward compatibility
		else:
			groups = ["saashq:"]

		for group in groups:
			failure = wrench.run(f"{sudo}supervisorctl restart {group}", _raise=_raise)
			if failure:
				log(
					f"restarting supervisor group `{group}` failed. Use `wrench restart` to retry.",
					level=3,
				)


def restart_systemd_processes(wrench_path=".", web_workers=False, _raise=True):
	wrench_name = get_wrench_name(wrench_path)
	exec_cmd(
		f"sudo systemctl stop -- $(systemctl show -p Requires {wrench_name}.target | cut"
		" -d= -f2)",
		_raise=_raise,
	)
	exec_cmd(
		f"sudo systemctl start -- $(systemctl show -p Requires {wrench_name}.target |"
		" cut -d= -f2)",
		_raise=_raise,
	)


def restart_process_manager(wrench_path=".", web_workers=False):
	# only overmind has the restart feature, not sure other supported procmans do
	if which("overmind") and os.path.exists(os.path.join(wrench_path, ".overmind.sock")):
		worker = "web" if web_workers else ""
		exec_cmd(f"overmind restart {worker}", cwd=wrench_path)


def build_assets(wrench_path=".", app=None, using_cached=False):
	command = "wrench build"
	if app:
		command += f" --app {app}"

	env = {"WRENCH_DEVELOPER": "1"}
	if using_cached:
		env["USING_CACHED"] = "1"

	exec_cmd(command, cwd=wrench_path, env=env)


def handle_version_upgrade(version_upgrade, wrench_path, force, reset, conf):
	from wrench.utils import log, pause_exec

	if version_upgrade[0]:
		if force:
			log(
				"""Force flag has been used for a major version change in Saashq and it's apps.
This will take significant time to migrate and might break custom apps.""",
				level=3,
			)
		else:
			print(
				f"""This update will cause a major version change in Saashq/ERPNexus from {version_upgrade[1]} to {version_upgrade[2]}.
This would take significant time to migrate and might break custom apps."""
			)
			click.confirm("Do you want to continue?", abort=True)

	if not reset and conf.get("shallow_clone"):
		log(
			"""shallow_clone is set in your wrench config.
However without passing the --reset flag, your repositories will be unshallowed.
To avoid this, cancel this operation and run `wrench update --reset`.

Consider the consequences of `git reset --hard` on your apps before you run that.
To avoid seeing this warning, set shallow_clone to false in your common_site_config.json
		""",
			level=3,
		)
		pause_exec(seconds=10)

	if version_upgrade[0] or (not version_upgrade[0] and force):
		validate_upgrade(version_upgrade[1], version_upgrade[2], wrench_path=wrench_path)


def update(
	pull: bool = False,
	apps: str = None,
	patch: bool = False,
	build: bool = False,
	requirements: bool = False,
	backup: bool = True,
	compile: bool = True,
	force: bool = False,
	reset: bool = False,
	restart_supervisor: bool = False,
	restart_systemd: bool = False,
):
	"""command: wrench update"""
	import re

	from wrench import patches
	from wrench.app import pull_apps
	from wrench.wrench import Wrench
	from wrench.config.common_site_config import update_config
	from wrench.exceptions import CannotUpdateReleaseWrench
	from wrench.utils.app import is_version_upgrade
	from wrench.utils.system import backup_all_sites

	wrench_path = os.path.abspath(".")
	wrench = Wrench(wrench_path)
	patches.run(wrench_path=wrench_path)
	conf = wrench.conf

	if conf.get("release_wrench"):
		raise CannotUpdateReleaseWrench("Release wrench detected, cannot update!")

	if not (pull or patch or build or requirements):
		pull, patch, build, requirements = True, True, True, True

	if apps and pull:
		apps = [app.strip() for app in re.split(",| ", apps) if app]
	else:
		apps = []

	validate_branch()

	version_upgrade = is_version_upgrade()
	handle_version_upgrade(version_upgrade, wrench_path, force, reset, conf)

	conf.update({"maintenance_mode": 1, "pause_scheduler": 1})
	update_config(conf, wrench_path=wrench_path)

	if backup:
		print("Backing up sites...")
		backup_all_sites(wrench_path=wrench_path)

	if pull:
		print("Updating apps source...")
		pull_apps(apps=apps, wrench_path=wrench_path, reset=reset)

	if requirements:
		print("Setting up requirements...")
		wrench.setup.requirements()

	if patch:
		print("Patching sites...")
		patch_sites(wrench_path=wrench_path)

	if build:
		print("Building assets...")
		wrench.build()

	if version_upgrade[0] or (not version_upgrade[0] and force):
		post_upgrade(version_upgrade[1], version_upgrade[2], wrench_path=wrench_path)

	wrench.reload(web=False, supervisor=restart_supervisor, systemd=restart_systemd)

	conf.update({"maintenance_mode": 0, "pause_scheduler": 0})
	update_config(conf, wrench_path=wrench_path)

	print(
		"_" * 80 + "\nWrench: Deployment tool for Saashq and Saashq Applications"
		" (https://saashq.org/wrench).\nOpen source depends on your contributions, so do"
		" give back by submitting bug reports, patches and fixes and be a part of the"
		" community :)"
	)


def clone_apps_from(wrench_path, clone_from, update_app=True):
	from wrench.app import install_app

	print(f"Copying apps from {clone_from}...")
	subprocess.check_output(["cp", "-R", os.path.join(clone_from, "apps"), wrench_path])

	node_modules_path = os.path.join(clone_from, "node_modules")
	if os.path.exists(node_modules_path):
		print(f"Copying node_modules from {clone_from}...")
		subprocess.check_output(["cp", "-R", node_modules_path, wrench_path])

	def setup_app(app):
		# run git reset --hard in each branch, pull latest updates and install_app
		app_path = os.path.join(wrench_path, "apps", app)

		# remove .egg-ino
		subprocess.check_output(["rm", "-rf", app + ".egg-info"], cwd=app_path)

		if update_app and os.path.exists(os.path.join(app_path, ".git")):
			remotes = subprocess.check_output(["git", "remote"], cwd=app_path).strip().split()
			if "upstream" in remotes:
				remote = "upstream"
			else:
				remote = remotes[0]
			print(f"Cleaning up {app}")
			branch = subprocess.check_output(
				["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=app_path
			).strip()
			subprocess.check_output(["git", "reset", "--hard"], cwd=app_path)
			subprocess.check_output(["git", "pull", "--rebase", remote, branch], cwd=app_path)

		install_app(app, wrench_path, restart_wrench=False)

	with open(os.path.join(clone_from, "sites", "apps.txt")) as f:
		apps = f.read().splitlines()

	for app in apps:
		setup_app(app)


def remove_backups_crontab(wrench_path="."):
	from crontab import CronTab

	from wrench.wrench import Wrench

	logger.log("removing backup cronjob")

	wrench_dir = os.path.abspath(wrench_path)
	user = Wrench(wrench_dir).conf.get("saashq_user")
	logfile = os.path.join(wrench_dir, "logs", "backup.log")
	system_crontab = CronTab(user=user)
	backup_command = f"cd {wrench_dir} && {sys.argv[0]} --verbose --site all backup"
	job_command = f"{backup_command} >> {logfile} 2>&1"

	system_crontab.remove_all(command=job_command)


def set_mariadb_host(host, wrench_path="."):
	update_common_site_config({"db_host": host}, wrench_path=wrench_path)


def set_redis_cache_host(host, wrench_path="."):
	update_common_site_config({"redis_cache": f"redis://{host}"}, wrench_path=wrench_path)


def set_redis_queue_host(host, wrench_path="."):
	update_common_site_config({"redis_queue": f"redis://{host}"}, wrench_path=wrench_path)


def set_redis_socketio_host(host, wrench_path="."):
	update_common_site_config({"redis_socketio": f"redis://{host}"}, wrench_path=wrench_path)


def update_common_site_config(ddict, wrench_path="."):
	filename = os.path.join(wrench_path, "sites", "common_site_config.json")

	if os.path.exists(filename):
		with open(filename) as f:
			content = json.load(f)

	else:
		content = {}

	content.update(ddict)
	with open(filename, "w") as f:
		json.dump(content, f, indent=1, sort_keys=True)


def validate_app_installed_on_sites(app, wrench_path="."):
	print("Checking if app installed on active sites...")
	ret = check_app_installed(app, wrench_path=wrench_path)

	if ret is None:
		check_app_installed_legacy(app, wrench_path=wrench_path)
	else:
		return ret


def check_app_installed(app, wrench_path="."):
	try:
		out = subprocess.check_output(
			["wrench", "--site", "all", "list-apps", "--format", "json"],
			stderr=open(os.devnull, "wb"),
			cwd=wrench_path,
		).decode("utf-8")
	except subprocess.CalledProcessError:
		return None

	try:
		apps_sites_dict = json.loads(out)
	except JSONDecodeError:
		return None

	for site, apps in apps_sites_dict.items():
		if app in apps:
			raise ValidationError(f"Cannot remove, app is installed on site: {site}")


def check_app_installed_legacy(app, wrench_path="."):
	site_path = os.path.join(wrench_path, "sites")

	for site in os.listdir(site_path):
		req_file = os.path.join(site_path, site, "site_config.json")
		if os.path.exists(req_file):
			out = subprocess.check_output(
				["wrench", "--site", site, "list-apps"], cwd=wrench_path
			).decode("utf-8")
			if re.search(r"\b" + app + r"\b", out):
				print(f"Cannot remove, app is installed on site: {site}")
				sys.exit(1)


def validate_branch():
	from wrench.wrench import Wrench
	from wrench.utils.app import get_current_branch

	apps = Wrench(".").apps

	installed_apps = set(apps)
	check_apps = {"saashq", "erpnexus"}
	intersection_apps = installed_apps.intersection(check_apps)

	for app in intersection_apps:
		branch = get_current_branch(app)

		if branch == "master":
			print(
				"""'master' branch is renamed to 'version-11' since 'version-12' release.
As of January 2020, the following branches are
version		Saashq			ERPNexus
11		version-11		version-11
12		version-12		version-12
13		version-13		version-13
14		develop			develop

Please switch to new branches to get future updates.
To switch to your required branch, run the following commands: wrench switch-to-branch [branch-name]"""
			)

			sys.exit(1)


def cache_helper(clear=False, remove_app="", remove_key="") -> None:
	can_remove = bool(remove_key or remove_app)
	if not clear and not can_remove:
		cache_list()
	elif can_remove:
		cache_remove(remove_app, remove_key)
	elif clear:
		cache_clear()
	else:
		pass  # unreachable


def cache_list() -> None:
	from datetime import datetime

	tot_size = 0
	tot_items = 0

	printed_header = False
	for item in get_wrench_cache_path("apps").iterdir():
		if item.suffix not in [".tar", ".tgz"]:
			continue

		stat = item.stat()
		size_mb = stat.st_size / 1_000_000
		created = datetime.fromtimestamp(stat.st_ctime)
		accessed = datetime.fromtimestamp(stat.st_atime)

		app = item.name.split(".")[0]
		tot_items += 1
		tot_size += stat.st_size
		compressed = item.suffix == ".tgz"

		if not printed_header:
			click.echo(
				f"{'APP':15}  "
				f"{'FILE':90}  "
				f"{'SIZE':>13}  "
				f"{'COMPRESSED'}  "
				f"{'CREATED':19}  "
				f"{'ACCESSED':19}  "
			)
			printed_header = True

		click.echo(
			f"{app:15}  "
			f"{item.name:90}  "
			f"{size_mb:10.3f} MB  "
			f"{str(compressed):10}  "
			f"{created:%Y-%m-%d %H:%M:%S}  "
			f"{accessed:%Y-%m-%d %H:%M:%S}  "
		)

	if tot_items:
		click.echo(f"Total size {tot_size / 1_000_000:.3f} MB belonging to {tot_items} items")
	else:
		click.echo("No cached items")


def cache_remove(app: str = "", key: str = "") -> None:
	rem_items = 0
	rem_size = 0
	for item in get_wrench_cache_path("apps").iterdir():
		if not should_remove_item(item, app, key):
			continue

		rem_items += 1
		rem_size += item.stat().st_size
		item.unlink(True)
		click.echo(f"Removed {item.name}")

	if rem_items:
		click.echo(f"Cleared {rem_size / 1_000_000:.3f} MB belonging to {rem_items} items")
	else:
		click.echo("No items removed")


def should_remove_item(item: Path, app: str, key: str) -> bool:
	if item.suffix not in [".tar", ".tgz"]:
		return False

	name = item.name
	if app and key and name.startswith(f"{app}-{key[:10]}."):
		return True

	if app and name.startswith(f"{app}-"):
		return True

	if key and f"-{key[:10]}." in name:
		return True

	return False


def cache_clear() -> None:
	cache_path = get_wrench_cache_path("apps")
	tot_items = len(os.listdir(cache_path))
	if not tot_items:
		click.echo("No cached items")
		return

	tot_size = get_dir_size(cache_path)
	shutil.rmtree(cache_path)

	if tot_items:
		click.echo(f"Cleared {tot_size / 1_000_000:.3f} MB belonging to {tot_items} items")


def get_dir_size(p: Path) -> int:
	return sum(i.stat(follow_symlinks=False).st_size for i in p.iterdir())
