import os
import shutil
import subprocess
import unittest

from wrench.app import App
from wrench.wrench import Wrench
from wrench.exceptions import InvalidRemoteException
from wrench.utils import is_valid_saashq_branch


class TestUtils(unittest.TestCase):
	def test_app_utils(self):
		git_url = "https://github.com/saashqdev/saashq"
		branch = "develop"
		app = App(name=git_url, branch=branch, wrench=Wrench("."))
		self.assertTrue(
			all(
				[
					app.name == git_url,
					app.branch == branch,
					app.tag == branch,
					app.is_url is True,
					app.on_disk is False,
					app.org == "saashq",
					app.url == git_url,
				]
			)
		)

	def test_is_valid_saashq_branch(self):
		with self.assertRaises(InvalidRemoteException):
			is_valid_saashq_branch(
				"https://github.com/saashqdev/saashq.git", saashq_branch="random-branch"
			)
			is_valid_saashq_branch(
				"https://github.com/random/random.git", saashq_branch="random-branch"
			)

		is_valid_saashq_branch(
			"https://github.com/saashqdev/saashq.git", saashq_branch="develop"
		)
		is_valid_saashq_branch(
			"https://github.com/saashqdev/saashq.git", saashq_branch="v13.29.0"
		)

	def test_app_states(self):
		wrench_dir = "./sandbox"
		sites_dir = os.path.join(wrench_dir, "sites")

		if not os.path.exists(sites_dir):
			os.makedirs(sites_dir)

		fake_wrench = Wrench(wrench_dir)

		self.assertTrue(hasattr(fake_wrench.apps, "states"))

		fake_wrench.apps.states = {
			"saashq": {
				"resolution": {"branch": "develop", "commit_hash": "234rwefd"},
				"version": "14.0.0-dev",
			}
		}
		fake_wrench.apps.update_apps_states()

		self.assertEqual(fake_wrench.apps.states, {})

		saashq_path = os.path.join(wrench_dir, "apps", "saashq")

		os.makedirs(os.path.join(saashq_path, "saashq"))

		subprocess.run(["git", "init"], cwd=saashq_path, capture_output=True, check=True)

		with open(os.path.join(saashq_path, "saashq", "__init__.py"), "w+") as f:
			f.write("__version__ = '11.0'")

		subprocess.run(["git", "add", "."], cwd=saashq_path, capture_output=True, check=True)
		subprocess.run(
			["git", "config", "user.email", "wrench-test_app_states@gha.com"],
			cwd=saashq_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "config", "user.name", "App States Test"],
			cwd=saashq_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "commit", "-m", "temp"], cwd=saashq_path, capture_output=True, check=True
		)

		fake_wrench.apps.update_apps_states(app_name="saashq")

		self.assertIn("saashq", fake_wrench.apps.states)
		self.assertIn("version", fake_wrench.apps.states["saashq"])
		self.assertEqual("11.0", fake_wrench.apps.states["saashq"]["version"])

		shutil.rmtree(wrench_dir)

	def test_ssh_ports(self):
		app = App("git@github.com:22:saashq/saashq")
		self.assertEqual(
			(app.use_ssh, app.org, app.repo, app.app_name), (True, "saashq", "saashq", "saashq")
		)
