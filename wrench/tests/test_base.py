# imports - standard imports
import getpass
import json
import os
import shutil
import subprocess
import sys
import traceback
import unittest

# imports - module imports
from wrench.utils import paths_in_wrench, exec_cmd
from wrench.utils.system import init
from wrench.wrench import Wrench

PYTHON_VER = sys.version_info

SAASHQ_BRANCH = "version-13-hotfix"
if PYTHON_VER.major == 3:
	if PYTHON_VER.minor >= 10:
		SAASHQ_BRANCH = "develop"


class TestWrenchBase(unittest.TestCase):
	def setUp(self):
		self.wrenches_path = "."
		self.wrenches = []

	def tearDown(self):
		for wrench_name in self.wrenches:
			wrench_path = os.path.join(self.wrenches_path, wrench_name)
			wrench = Wrench(wrench_path)
			mariadb_password = (
				"travis"
				if os.environ.get("CI")
				else getpass.getpass(prompt="Enter MariaDB root Password: ")
			)

			if wrench.exists:
				for site in wrench.sites:
					subprocess.call(
						[
							"wrench",
							"drop-site",
							site,
							"--force",
							"--no-backup",
							"--root-password",
							mariadb_password,
						],
						cwd=wrench_path,
					)
				shutil.rmtree(wrench_path, ignore_errors=True)

	def assert_folders(self, wrench_name):
		for folder in paths_in_wrench:
			self.assert_exists(wrench_name, folder)
		self.assert_exists(wrench_name, "apps", "saashq")

	def assert_virtual_env(self, wrench_name):
		wrench_path = os.path.abspath(wrench_name)
		python_path = os.path.abspath(os.path.join(wrench_path, "env", "bin", "python"))
		self.assertTrue(python_path.startswith(wrench_path))
		for subdir in ("bin", "lib", "share"):
			self.assert_exists(wrench_name, "env", subdir)

	def assert_config(self, wrench_name):
		for config, search_key in (
			("redis_queue.conf", "redis_queue.rdb"),
			("redis_cache.conf", "redis_cache.rdb"),
		):

			self.assert_exists(wrench_name, "config", config)

			with open(os.path.join(wrench_name, "config", config)) as f:
				self.assertTrue(search_key in f.read())

	def assert_common_site_config(self, wrench_name, expected_config):
		common_site_config_path = os.path.join(
			self.wrenches_path, wrench_name, "sites", "common_site_config.json"
		)
		self.assertTrue(os.path.exists(common_site_config_path))

		with open(common_site_config_path) as f:
			config = json.load(f)

		for key, value in list(expected_config.items()):
			self.assertEqual(config.get(key), value)

	def assert_exists(self, *args):
		self.assertTrue(os.path.exists(os.path.join(*args)))

	def new_site(self, site_name, wrench_name):
		new_site_cmd = ["wrench", "new-site", site_name, "--admin-password", "admin"]

		if os.environ.get("CI"):
			new_site_cmd.extend(["--mariadb-root-password", "travis"])

		subprocess.call(new_site_cmd, cwd=os.path.join(self.wrenches_path, wrench_name))

	def init_wrench(self, wrench_name, **kwargs):
		self.wrenches.append(wrench_name)
		saashq_tmp_path = "/tmp/saashq"

		if not os.path.exists(saashq_tmp_path):
			exec_cmd(
				f"git clone https://github.com/saashqdev/saashq -b {SAASHQ_BRANCH} --depth 1 --origin upstream {saashq_tmp_path}"
			)

		kwargs.update(
			dict(
				python=sys.executable,
				no_procfile=True,
				no_backups=True,
				saashq_path=saashq_tmp_path,
			)
		)

		if not os.path.exists(os.path.join(self.wrenches_path, wrench_name)):
			init(wrench_name, **kwargs)
			exec_cmd(
				"git remote set-url upstream https://github.com/saashqdev/saashq",
				cwd=os.path.join(self.wrenches_path, wrench_name, "apps", "saashq"),
			)

	def file_exists(self, path):
		if os.environ.get("CI"):
			return not subprocess.call(["sudo", "test", "-f", path])
		return os.path.isfile(path)

	def get_traceback(self):
		exc_type, exc_value, exc_tb = sys.exc_info()
		trace_list = traceback.format_exception(exc_type, exc_value, exc_tb)
		return "".join(str(t) for t in trace_list)
