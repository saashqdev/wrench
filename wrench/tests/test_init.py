# imports - standard imports
import json
import os
import subprocess
import unittest

# imports - third paty imports
import git

# imports - module imports
from wrench.utils import exec_cmd
from wrench.app import App
from wrench.tests.test_base import SAASHQ_BRANCH, TestWrenchBase
from wrench.wrench import Wrench


# changed from saashq_theme because it wasn't maintained and incompatible,
# chat app & wiki was breaking too. hopefully saashq_docs will be maintained
# for longer since docs.erpnexus.com is powered by it ;)
TEST_SAASHQ_APP = "saashq_docs"


class TestWrenchInit(TestWrenchBase):
	def test_utils(self):
		self.assertEqual(subprocess.call("wrench"), 0)

	def test_init(self, wrench_name="test-wrench", **kwargs):
		self.init_wrench(wrench_name, **kwargs)
		app = App("file:///tmp/saashq")
		self.assertTupleEqual(
			(app.mount_path, app.url, app.repo, app.app_name, app.org),
			("/tmp/saashq", "file:///tmp/saashq", "saashq", "saashq", "saashq"),
		)
		self.assert_folders(wrench_name)
		self.assert_virtual_env(wrench_name)
		self.assert_config(wrench_name)
		test_wrench = Wrench(wrench_name)
		app = App("saashq", wrench=test_wrench)
		self.assertEqual(app.from_apps, True)

	def basic(self):
		try:
			self.test_init()
		except Exception:
			print(self.get_traceback())

	def test_multiple_wrenches(self):
		for wrench_name in ("test-wrench-1", "test-wrench-2"):
			self.init_wrench(wrench_name, skip_assets=True)

		self.assert_common_site_config(
			"test-wrench-1",
			{
				"webserver_port": 8000,
				"socketio_port": 9000,
				"file_watcher_port": 6787,
				"redis_queue": "redis://127.0.0.1:11000",
				"redis_socketio": "redis://127.0.0.1:13000",
				"redis_cache": "redis://127.0.0.1:13000",
			},
		)

		self.assert_common_site_config(
			"test-wrench-2",
			{
				"webserver_port": 8001,
				"socketio_port": 9001,
				"file_watcher_port": 6788,
				"redis_queue": "redis://127.0.0.1:11001",
				"redis_socketio": "redis://127.0.0.1:13001",
				"redis_cache": "redis://127.0.0.1:13001",
			},
		)

	def test_new_site(self):
		wrench_name = "test-wrench"
		site_name = "test-site.local"
		wrench_path = os.path.join(self.wrenches_path, wrench_name)
		site_path = os.path.join(wrench_path, "sites", site_name)
		site_config_path = os.path.join(site_path, "site_config.json")

		self.init_wrench(wrench_name)
		self.new_site(site_name, wrench_name)

		self.assertTrue(os.path.exists(site_path))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "backups")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "files")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "public", "files")))
		self.assertTrue(os.path.exists(site_config_path))

		with open(site_config_path) as f:
			site_config = json.loads(f.read())

			for key in ("db_name", "db_password"):
				self.assertTrue(key in site_config)
				self.assertTrue(site_config[key])

	def test_get_app(self):
		self.init_wrench("test-wrench", skip_assets=True)
		wrench_path = os.path.join(self.wrenches_path, "test-wrench")
		exec_cmd(f"wrench get-app {TEST_SAASHQ_APP} --skip-assets", cwd=wrench_path)
		self.assertTrue(os.path.exists(os.path.join(wrench_path, "apps", TEST_SAASHQ_APP)))
		app_installed_in_env = TEST_SAASHQ_APP in subprocess.check_output(
			["wrench", "pip", "freeze"], cwd=wrench_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

	@unittest.skipIf(SAASHQ_BRANCH != "develop", "only for develop branch")
	def test_get_app_resolve_deps(self):
		SAASHQ_APP = "healthcare"
		self.init_wrench("test-wrench", skip_assets=True)
		wrench_path = os.path.join(self.wrenches_path, "test-wrench")
		exec_cmd(f"wrench get-app {SAASHQ_APP} --resolve-deps --skip-assets", cwd=wrench_path)
		self.assertTrue(os.path.exists(os.path.join(wrench_path, "apps", SAASHQ_APP)))

		states_path = os.path.join(wrench_path, "sites", "apps.json")
		self.assertTrue(os.path.exists(states_path))

		with open(states_path) as f:
			states = json.load(f)

		self.assertTrue(SAASHQ_APP in states)

	def test_install_app(self):
		wrench_name = "test-wrench"
		site_name = "install-app.test"
		wrench_path = os.path.join(self.wrenches_path, "test-wrench")

		self.init_wrench(wrench_name, skip_assets=True)
		exec_cmd(
			f"wrench get-app {TEST_SAASHQ_APP} --branch master --skip-assets", cwd=wrench_path
		)

		self.assertTrue(os.path.exists(os.path.join(wrench_path, "apps", TEST_SAASHQ_APP)))

		# check if app is installed
		app_installed_in_env = TEST_SAASHQ_APP in subprocess.check_output(
			["wrench", "pip", "freeze"], cwd=wrench_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

		# create and install app on site
		self.new_site(site_name, wrench_name)
		installed_app = not exec_cmd(
			f"wrench --site {site_name} install-app {TEST_SAASHQ_APP}",
			cwd=wrench_path,
			_raise=False,
		)

		if installed_app:
			app_installed_on_site = subprocess.check_output(
				["wrench", "--site", site_name, "list-apps"], cwd=wrench_path
			).decode("utf8")
			self.assertTrue(TEST_SAASHQ_APP in app_installed_on_site)

	def test_remove_app(self):
		self.init_wrench("test-wrench", skip_assets=True)
		wrench_path = os.path.join(self.wrenches_path, "test-wrench")

		exec_cmd(
			f"wrench get-app {TEST_SAASHQ_APP} --branch master --overwrite --skip-assets",
			cwd=wrench_path,
		)
		exec_cmd(f"wrench remove-app {TEST_SAASHQ_APP}", cwd=wrench_path)

		with open(os.path.join(wrench_path, "sites", "apps.txt")) as f:
			self.assertFalse(TEST_SAASHQ_APP in f.read())
		self.assertFalse(
			TEST_SAASHQ_APP
			in subprocess.check_output(["wrench", "pip", "freeze"], cwd=wrench_path).decode("utf8")
		)
		self.assertFalse(os.path.exists(os.path.join(wrench_path, "apps", TEST_SAASHQ_APP)))

	def test_switch_to_branch(self):
		self.init_wrench("test-wrench", skip_assets=True)
		wrench_path = os.path.join(self.wrenches_path, "test-wrench")
		app_path = os.path.join(wrench_path, "apps", "saashq")

		# * chore: change to 14 when avalible
		prevoius_branch = "version-13"
		if SAASHQ_BRANCH != "develop":
			# assuming we follow `version-#`
			prevoius_branch = f"version-{int(SAASHQ_BRANCH.split('-')[1]) - 1}"

		successful_switch = not exec_cmd(
			f"wrench switch-to-branch {prevoius_branch} saashq --upgrade",
			cwd=wrench_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(prevoius_branch, app_branch_after_switch)

		successful_switch = not exec_cmd(
			f"wrench switch-to-branch {SAASHQ_BRANCH} saashq --upgrade",
			cwd=wrench_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_second_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(SAASHQ_BRANCH, app_branch_after_second_switch)


if __name__ == "__main__":
	unittest.main()
