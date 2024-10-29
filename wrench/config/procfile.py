import os
import platform

import click

import wrench
from wrench.app import use_rq
from wrench.wrench import Wrench
from wrench.utils import which


def setup_procfile(wrench_path, yes=False, skip_redis=False):
	config = Wrench(wrench_path).conf
	procfile_path = os.path.join(wrench_path, "Procfile")

	is_mac = platform.system() == "Darwin"
	if not yes and os.path.exists(procfile_path):
		click.confirm(
			"A Procfile already exists and this will overwrite it. Do you want to continue?",
			abort=True,
		)

	procfile = (
		wrench.config.env()
		.get_template("Procfile")
		.render(
			node=which("node") or which("nodejs"),
			use_rq=use_rq(wrench_path),
			webserver_port=config.get("webserver_port"),
			CI=os.environ.get("CI"),
			skip_redis=skip_redis,
			workers=config.get("workers", {}),
			is_mac=is_mac,
		)
	)

	with open(procfile_path, "w") as f:
		f.write(procfile)
