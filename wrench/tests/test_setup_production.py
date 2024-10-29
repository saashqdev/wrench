# imports - standard imports
import getpass
import os
import pathlib
import re
import subprocess
import time
import unittest

# imports - module imports
from wrench.utils import exec_cmd, get_cmd_output, which
from wrench.config.production_setup import get_supervisor_confdir
from wrench.tests.test_base import TestWrenchBase


class TestSetupProduction(TestWrenchBase):
	def test_setup_production(self):
		user = getpass.getuser()

		for wrench_name in ("test-wrench-1", "test-wrench-2"):
			wrench_path = os.path.join(os.path.abspath(self.wrenches_path), wrench_name)
			self.init_wrench(wrench_name)
			exec_cmd(f"sudo wrench setup production {user} --yes", cwd=wrench_path)
			self.assert_nginx_config(wrench_name)
			self.assert_supervisor_config(wrench_name)
			self.assert_supervisor_process(wrench_name)

		self.assert_nginx_process()
		exec_cmd(f"sudo wrench setup sudoers {user}")
		self.assert_sudoers(user)

		for wrench_name in self.wrenches:
			wrench_path = os.path.join(os.path.abspath(self.wrenches_path), wrench_name)
			exec_cmd("sudo wrench disable-production", cwd=wrench_path)

	def production(self):
		try:
			self.test_setup_production()
		except Exception:
			print(self.get_traceback())

	def assert_nginx_config(self, wrench_name):
		conf_src = os.path.join(
			os.path.abspath(self.wrenches_path), wrench_name, "config", "nginx.conf"
		)
		conf_dest = f"/etc/nginx/conf.d/{wrench_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			for key in (
				f"upstream {wrench_name}-saashq",
				f"upstream {wrench_name}-socketio-server",
			):
				self.assertTrue(key in f)

	def assert_nginx_process(self):
		out = get_cmd_output("sudo nginx -t 2>&1")
		self.assertTrue(
			"nginx: configuration file /etc/nginx/nginx.conf test is successful" in out
		)

	def assert_sudoers(self, user):
		sudoers_file = "/etc/sudoers.d/saashq"
		service = which("service")
		nginx = which("nginx")

		self.assertTrue(self.file_exists(sudoers_file))

		if os.environ.get("CI"):
			sudoers = subprocess.check_output(["sudo", "cat", sudoers_file]).decode("utf-8")
		else:
			sudoers = pathlib.Path(sudoers_file).read_text()
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {service} nginx *" in sudoers)
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {nginx}" in sudoers)

	def assert_supervisor_config(self, wrench_name, use_rq=True):
		conf_src = os.path.join(
			os.path.abspath(self.wrenches_path), wrench_name, "config", "supervisor.conf"
		)

		supervisor_conf_dir = get_supervisor_confdir()
		conf_dest = f"{supervisor_conf_dir}/{wrench_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			tests = [
				f"program:{wrench_name}-saashq-web",
				f"program:{wrench_name}-redis-cache",
				f"program:{wrench_name}-redis-queue",
				f"group:{wrench_name}-web",
				f"group:{wrench_name}-workers",
				f"group:{wrench_name}-redis",
			]

			if not os.environ.get("CI"):
				tests.append(f"program:{wrench_name}-node-socketio")

			if use_rq:
				tests.extend(
					[
						f"program:{wrench_name}-saashq-schedule",
						f"program:{wrench_name}-saashq-default-worker",
						f"program:{wrench_name}-saashq-short-worker",
						f"program:{wrench_name}-saashq-long-worker",
					]
				)

			else:
				tests.extend(
					[
						f"program:{wrench_name}-saashq-workerbeat",
						f"program:{wrench_name}-saashq-worker",
						f"program:{wrench_name}-saashq-longjob-worker",
						f"program:{wrench_name}-saashq-async-worker",
					]
				)

			for key in tests:
				self.assertTrue(key in f)

	def assert_supervisor_process(self, wrench_name, use_rq=True, disable_production=False):
		out = get_cmd_output("supervisorctl status")

		while "STARTING" in out:
			print("Waiting for all processes to start...")
			time.sleep(10)
			out = get_cmd_output("supervisorctl status")

		tests = [
			r"{wrench_name}-web:{wrench_name}-saashq-web[\s]+RUNNING",
			# Have commented for the time being. Needs to be uncommented later on. Wrench is failing on travis because of this.
			# It works on one wrench and fails on another.giving FATAL or BACKOFF (Exited too quickly (process log may have details))
			# "{wrench_name}-web:{wrench_name}-node-socketio[\s]+RUNNING",
			r"{wrench_name}-redis:{wrench_name}-redis-cache[\s]+RUNNING",
			r"{wrench_name}-redis:{wrench_name}-redis-queue[\s]+RUNNING",
		]

		if use_rq:
			tests.extend(
				[
					r"{wrench_name}-workers:{wrench_name}-saashq-schedule[\s]+RUNNING",
					r"{wrench_name}-workers:{wrench_name}-saashq-default-worker-0[\s]+RUNNING",
					r"{wrench_name}-workers:{wrench_name}-saashq-short-worker-0[\s]+RUNNING",
					r"{wrench_name}-workers:{wrench_name}-saashq-long-worker-0[\s]+RUNNING",
				]
			)

		else:
			tests.extend(
				[
					r"{wrench_name}-workers:{wrench_name}-saashq-workerbeat[\s]+RUNNING",
					r"{wrench_name}-workers:{wrench_name}-saashq-worker[\s]+RUNNING",
					r"{wrench_name}-workers:{wrench_name}-saashq-longjob-worker[\s]+RUNNING",
					r"{wrench_name}-workers:{wrench_name}-saashq-async-worker[\s]+RUNNING",
				]
			)

		for key in tests:
			if disable_production:
				self.assertFalse(re.search(key, out))
			else:
				self.assertTrue(re.search(key, out))


if __name__ == "__main__":
	unittest.main()
