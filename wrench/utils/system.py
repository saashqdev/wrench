# imports - standard imports
import grp
import os
import pwd
import shutil
import sys

# imports - module imports
import wrench
from wrench.utils import (
	exec_cmd,
	get_process_manager,
	log,
	run_saashq_cmd,
	sudoers_file,
	which,
	is_valid_saashq_branch,
)
from wrench.utils.wrench import build_assets, clone_apps_from
from wrench.utils.render import job


@job(title="Initializing Wrench {path}", success="Wrench {path} initialized")
def init(
	path,
	apps_path=None,
	no_procfile=False,
	no_backups=False,
	saashq_path=None,
	saashq_branch=None,
	verbose=False,
	clone_from=None,
	skip_redis_config_generation=False,
	clone_without_update=False,
	skip_assets=False,
	python="python3",
	install_app=None,
	dev=False,
):
	"""Initialize a new wrench directory

	* create a wrench directory in the given path
	* setup logging for the wrench
	* setup env for the wrench
	* setup config (dir/pids/redis/procfile) for the wrench
	* setup patches.txt for wrench
	* clone & install saashq
	        * install python & node dependencies
	        * build assets
	* setup backups crontab
	"""

	# Use print("\033c", end="") to clear entire screen after each step and re-render each list
	# another way => https://stackoverflow.com/a/44591228/10309266

	import wrench.cli
	from wrench.app import get_app, install_apps_from_path
	from wrench.wrench import Wrench

	verbose = wrench.cli.verbose or verbose

	wrench = Wrench(path)

	wrench.setup.dirs()
	wrench.setup.logging()
	wrench.setup.env(python=python)
	config = {}
	if dev:
		config["developer_mode"] = 1
	wrench.setup.config(
		redis=not skip_redis_config_generation,
		procfile=not no_procfile,
		additional_config=config,
	)
	wrench.setup.patches()

	# local apps
	if clone_from:
		clone_apps_from(
			wrench_path=path, clone_from=clone_from, update_app=not clone_without_update
		)

	# remote apps
	else:
		saashq_path = saashq_path or "https://github.com/saashqdev/saashq.git"
		is_valid_saashq_branch(saashq_path=saashq_path, saashq_branch=saashq_branch)
		get_app(
			saashq_path,
			branch=saashq_branch,
			wrench_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

		# fetch remote apps using config file - deprecate this!
		if apps_path:
			install_apps_from_path(apps_path, wrench_path=path)

	# getting app on wrench init using --install-app
	if install_app:
		get_app(
			install_app,
			branch=saashq_branch,
			wrench_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

	if not skip_assets:
		build_assets(wrench_path=path)

	if not no_backups:
		wrench.setup.backups()


def setup_sudoers(user):
	from wrench.config.lets_encrypt import get_certbot_path

	if not os.path.exists("/etc/sudoers.d"):
		os.makedirs("/etc/sudoers.d")

		set_permissions = not os.path.exists("/etc/sudoers")
		with open("/etc/sudoers", "a") as f:
			f.write("\n#includedir /etc/sudoers.d\n")

		if set_permissions:
			os.chmod("/etc/sudoers", 0o440)

	template = wrench.config.env().get_template("saashq_sudoers")
	saashq_sudoers = template.render(
		**{
			"user": user,
			"service": which("service"),
			"systemctl": which("systemctl"),
			"nginx": which("nginx"),
			"certbot": get_certbot_path(),
		}
	)

	with open(sudoers_file, "w") as f:
		f.write(saashq_sudoers)

	os.chmod(sudoers_file, 0o440)
	log(f"Sudoers was set up for user {user}", level=1)


def start(no_dev=False, concurrency=None, procfile=None, no_prefix=False, procman=None):
	program = which(procman) if procman else get_process_manager()
	if not program:
		raise Exception("No process manager found")

	os.environ["PYTHONUNBUFFERED"] = "true"
	if not no_dev:
		os.environ["DEV_SERVER"] = "true"

	command = [program, "start"]
	if concurrency:
		command.extend(["-c", concurrency])

	if procfile:
		command.extend(["-f", procfile])

	if no_prefix:
		command.extend(["--no-prefix"])

	os.execv(program, command)


def migrate_site(site, wrench_path="."):
	run_saashq_cmd("--site", site, "migrate", wrench_path=wrench_path)


def backup_site(site, wrench_path="."):
	run_saashq_cmd("--site", site, "backup", wrench_path=wrench_path)


def backup_all_sites(wrench_path="."):
	from wrench.wrench import Wrench

	for site in Wrench(wrench_path).sites:
		backup_site(site, wrench_path=wrench_path)


def fix_prod_setup_perms(wrench_path=".", saashq_user=None):
	from glob import glob
	from wrench.wrench import Wrench

	saashq_user = saashq_user or Wrench(wrench_path).conf.get("saashq_user")

	if not saashq_user:
		print("saashq user not set")
		sys.exit(1)

	globs = ["logs/*", "config/*"]
	for glob_name in globs:
		for path in glob(glob_name):
			uid = pwd.getpwnam(saashq_user).pw_uid
			gid = grp.getgrnam(saashq_user).gr_gid
			os.chown(path, uid, gid)


def setup_fonts():
	fonts_path = os.path.join("/tmp", "fonts")

	if os.path.exists("/etc/fonts_backup"):
		return

	exec_cmd("git clone https://github.com/saashqdev/fonts.git", cwd="/tmp")
	os.rename("/etc/fonts", "/etc/fonts_backup")
	os.rename("/usr/share/fonts", "/usr/share/fonts_backup")
	os.rename(os.path.join(fonts_path, "etc_fonts"), "/etc/fonts")
	os.rename(os.path.join(fonts_path, "usr_share_fonts"), "/usr/share/fonts")
	shutil.rmtree(fonts_path)
	exec_cmd("fc-cache -fv")
