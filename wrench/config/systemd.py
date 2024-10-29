# imports - standard imports
import getpass
import os

# imports - third partyimports
import click

# imports - module imports
import wrench
from wrench.app import use_rq
from wrench.wrench import Wrench
from wrench.config.common_site_config import (
	get_gunicorn_workers,
	update_config,
	get_default_max_requests,
	compute_max_requests_jitter,
)
from wrench.utils import exec_cmd, which, get_wrench_name


def generate_systemd_config(
	wrench_path,
	user=None,
	yes=False,
	stop=False,
	create_symlinks=False,
	delete_symlinks=False,
):

	if not user:
		user = getpass.getuser()

	config = Wrench(wrench_path).conf

	wrench_dir = os.path.abspath(wrench_path)
	wrench_name = get_wrench_name(wrench_path)

	if stop:
		exec_cmd(
			f"sudo systemctl stop -- $(systemctl show -p Requires {wrench_name}.target | cut -d= -f2)"
		)
		return

	if create_symlinks:
		_create_symlinks(wrench_path)
		return

	if delete_symlinks:
		_delete_symlinks(wrench_path)
		return

	number_of_workers = config.get("background_workers") or 1
	background_workers = []
	for i in range(number_of_workers):
		background_workers.append(
			get_wrench_name(wrench_path) + "-saashq-default-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_wrench_name(wrench_path) + "-saashq-short-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_wrench_name(wrench_path) + "-saashq-long-worker@" + str(i + 1) + ".service"
		)

	web_worker_count = config.get(
		"gunicorn_workers", get_gunicorn_workers()["gunicorn_workers"]
	)
	max_requests = config.get(
		"gunicorn_max_requests", get_default_max_requests(web_worker_count)
	)

	wrench_info = {
		"wrench_dir": wrench_dir,
		"sites_dir": os.path.join(wrench_dir, "sites"),
		"user": user,
		"use_rq": use_rq(wrench_path),
		"http_timeout": config.get("http_timeout", 120),
		"redis_server": which("redis-server"),
		"node": which("node") or which("nodejs"),
		"redis_cache_config": os.path.join(wrench_dir, "config", "redis_cache.conf"),
		"redis_queue_config": os.path.join(wrench_dir, "config", "redis_queue.conf"),
		"webserver_port": config.get("webserver_port", 8000),
		"gunicorn_workers": web_worker_count,
		"gunicorn_max_requests": max_requests,
		"gunicorn_max_requests_jitter": compute_max_requests_jitter(max_requests),
		"wrench_name": get_wrench_name(wrench_path),
		"worker_target_wants": " ".join(background_workers),
		"wrench_cmd": which("wrench"),
	}

	if not yes:
		click.confirm(
			"current systemd configuration will be overwritten. Do you want to continue?",
			abort=True,
		)

	setup_systemd_directory(wrench_path)
	setup_main_config(wrench_info, wrench_path)
	setup_workers_config(wrench_info, wrench_path)
	setup_web_config(wrench_info, wrench_path)
	setup_redis_config(wrench_info, wrench_path)

	update_config({"restart_systemd_on_update": False}, wrench_path=wrench_path)
	update_config({"restart_supervisor_on_update": False}, wrench_path=wrench_path)


def setup_systemd_directory(wrench_path):
	if not os.path.exists(os.path.join(wrench_path, "config", "systemd")):
		os.makedirs(os.path.join(wrench_path, "config", "systemd"))


def setup_main_config(wrench_info, wrench_path):
	# Main config
	wrench_template = wrench.config.env().get_template("systemd/saashq-wrench.target")
	wrench_config = wrench_template.render(**wrench_info)
	wrench_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + ".target"
	)

	with open(wrench_config_path, "w") as f:
		f.write(wrench_config)


def setup_workers_config(wrench_info, wrench_path):
	# Worker Group
	wrench_workers_target_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-workers.target"
	)
	wrench_default_worker_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-saashq-default-worker.service"
	)
	wrench_short_worker_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-saashq-short-worker.service"
	)
	wrench_long_worker_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-saashq-long-worker.service"
	)
	wrench_schedule_worker_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-saashq-schedule.service"
	)

	wrench_workers_target_config = wrench_workers_target_template.render(**wrench_info)
	wrench_default_worker_config = wrench_default_worker_template.render(**wrench_info)
	wrench_short_worker_config = wrench_short_worker_template.render(**wrench_info)
	wrench_long_worker_config = wrench_long_worker_template.render(**wrench_info)
	wrench_schedule_worker_config = wrench_schedule_worker_template.render(**wrench_info)

	wrench_workers_target_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + "-workers.target"
	)
	wrench_default_worker_config_path = os.path.join(
		wrench_path,
		"config",
		"systemd",
		wrench_info.get("wrench_name") + "-saashq-default-worker@.service",
	)
	wrench_short_worker_config_path = os.path.join(
		wrench_path,
		"config",
		"systemd",
		wrench_info.get("wrench_name") + "-saashq-short-worker@.service",
	)
	wrench_long_worker_config_path = os.path.join(
		wrench_path,
		"config",
		"systemd",
		wrench_info.get("wrench_name") + "-saashq-long-worker@.service",
	)
	wrench_schedule_worker_config_path = os.path.join(
		wrench_path,
		"config",
		"systemd",
		wrench_info.get("wrench_name") + "-saashq-schedule.service",
	)

	with open(wrench_workers_target_config_path, "w") as f:
		f.write(wrench_workers_target_config)

	with open(wrench_default_worker_config_path, "w") as f:
		f.write(wrench_default_worker_config)

	with open(wrench_short_worker_config_path, "w") as f:
		f.write(wrench_short_worker_config)

	with open(wrench_long_worker_config_path, "w") as f:
		f.write(wrench_long_worker_config)

	with open(wrench_schedule_worker_config_path, "w") as f:
		f.write(wrench_schedule_worker_config)


def setup_web_config(wrench_info, wrench_path):
	# Web Group
	wrench_web_target_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-web.target"
	)
	wrench_web_service_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-saashq-web.service"
	)
	wrench_node_socketio_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-node-socketio.service"
	)

	wrench_web_target_config = wrench_web_target_template.render(**wrench_info)
	wrench_web_service_config = wrench_web_service_template.render(**wrench_info)
	wrench_node_socketio_config = wrench_node_socketio_template.render(**wrench_info)

	wrench_web_target_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + "-web.target"
	)
	wrench_web_service_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + "-saashq-web.service"
	)
	wrench_node_socketio_config_path = os.path.join(
		wrench_path,
		"config",
		"systemd",
		wrench_info.get("wrench_name") + "-node-socketio.service",
	)

	with open(wrench_web_target_config_path, "w") as f:
		f.write(wrench_web_target_config)

	with open(wrench_web_service_config_path, "w") as f:
		f.write(wrench_web_service_config)

	with open(wrench_node_socketio_config_path, "w") as f:
		f.write(wrench_node_socketio_config)


def setup_redis_config(wrench_info, wrench_path):
	# Redis Group
	wrench_redis_target_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-redis.target"
	)
	wrench_redis_cache_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-redis-cache.service"
	)
	wrench_redis_queue_template = wrench.config.env().get_template(
		"systemd/saashq-wrench-redis-queue.service"
	)

	wrench_redis_target_config = wrench_redis_target_template.render(**wrench_info)
	wrench_redis_cache_config = wrench_redis_cache_template.render(**wrench_info)
	wrench_redis_queue_config = wrench_redis_queue_template.render(**wrench_info)

	wrench_redis_target_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + "-redis.target"
	)
	wrench_redis_cache_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + "-redis-cache.service"
	)
	wrench_redis_queue_config_path = os.path.join(
		wrench_path, "config", "systemd", wrench_info.get("wrench_name") + "-redis-queue.service"
	)

	with open(wrench_redis_target_config_path, "w") as f:
		f.write(wrench_redis_target_config)

	with open(wrench_redis_cache_config_path, "w") as f:
		f.write(wrench_redis_cache_config)

	with open(wrench_redis_queue_config_path, "w") as f:
		f.write(wrench_redis_queue_config)


def _create_symlinks(wrench_path):
	wrench_dir = os.path.abspath(wrench_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	config_path = os.path.join(wrench_dir, "config", "systemd")
	unit_files = get_unit_files(wrench_dir)
	for unit_file in unit_files:
		filename = "".join(unit_file)
		exec_cmd(
			f'sudo ln -s {config_path}/{filename} {etc_systemd_system}/{"".join(unit_file)}'
		)
	exec_cmd("sudo systemctl daemon-reload")


def _delete_symlinks(wrench_path):
	wrench_dir = os.path.abspath(wrench_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	unit_files = get_unit_files(wrench_dir)
	for unit_file in unit_files:
		exec_cmd(f'sudo rm {etc_systemd_system}/{"".join(unit_file)}')
	exec_cmd("sudo systemctl daemon-reload")


def get_unit_files(wrench_path):
	wrench_name = get_wrench_name(wrench_path)
	unit_files = [
		[wrench_name, ".target"],
		[wrench_name + "-workers", ".target"],
		[wrench_name + "-web", ".target"],
		[wrench_name + "-redis", ".target"],
		[wrench_name + "-saashq-default-worker@", ".service"],
		[wrench_name + "-saashq-short-worker@", ".service"],
		[wrench_name + "-saashq-long-worker@", ".service"],
		[wrench_name + "-saashq-schedule", ".service"],
		[wrench_name + "-saashq-web", ".service"],
		[wrench_name + "-node-socketio", ".service"],
		[wrench_name + "-redis-cache", ".service"],
		[wrench_name + "-redis-queue", ".service"],
	]
	return unit_files
