# imports - third party imports
import click

# imports - module imports
from wrench.utils.cli import (
	MultiCommandGroup,
	print_wrench_version,
	use_experimental_feature,
	setup_verbosity,
)


@click.group(cls=MultiCommandGroup)
@click.option(
	"--version",
	is_flag=True,
	is_eager=True,
	callback=print_wrench_version,
	expose_value=False,
)
@click.option(
	"--use-feature",
	is_eager=True,
	callback=use_experimental_feature,
	expose_value=False,
)
@click.option(
	"-v",
	"--verbose",
	is_flag=True,
	callback=setup_verbosity,
	expose_value=False,
)
def wrench_command(wrench_path="."):
	import wrench

	wrench.set_saashq_version(wrench_path=wrench_path)


from wrench.commands.make import (
	drop,
	exclude_app_for_update,
	get_app,
	include_app_for_update,
	init,
	new_app,
	pip,
	remove_app,
	validate_dependencies,
)

wrench_command.add_command(init)
wrench_command.add_command(drop)
wrench_command.add_command(get_app)
wrench_command.add_command(new_app)
wrench_command.add_command(remove_app)
wrench_command.add_command(exclude_app_for_update)
wrench_command.add_command(include_app_for_update)
wrench_command.add_command(pip)
wrench_command.add_command(validate_dependencies)


from wrench.commands.update import (
	retry_upgrade,
	switch_to_branch,
	switch_to_develop,
	update,
)

wrench_command.add_command(update)
wrench_command.add_command(retry_upgrade)
wrench_command.add_command(switch_to_branch)
wrench_command.add_command(switch_to_develop)


from wrench.commands.utils import (
	app_cache_helper,
	backup_all_sites,
	wrench_src,
	disable_production,
	download_translations,
	find_wrenches,
	migrate_env,
	renew_lets_encrypt,
	restart,
	set_mariadb_host,
	set_nginx_port,
	set_redis_cache_host,
	set_redis_queue_host,
	set_redis_socketio_host,
	set_ssl_certificate,
	set_ssl_certificate_key,
	set_url_root,
	start,
)

wrench_command.add_command(start)
wrench_command.add_command(restart)
wrench_command.add_command(set_nginx_port)
wrench_command.add_command(set_ssl_certificate)
wrench_command.add_command(set_ssl_certificate_key)
wrench_command.add_command(set_url_root)
wrench_command.add_command(set_mariadb_host)
wrench_command.add_command(set_redis_cache_host)
wrench_command.add_command(set_redis_queue_host)
wrench_command.add_command(set_redis_socketio_host)
wrench_command.add_command(download_translations)
wrench_command.add_command(backup_all_sites)
wrench_command.add_command(renew_lets_encrypt)
wrench_command.add_command(disable_production)
wrench_command.add_command(wrench_src)
wrench_command.add_command(find_wrenches)
wrench_command.add_command(migrate_env)
wrench_command.add_command(app_cache_helper)

from wrench.commands.setup import setup

wrench_command.add_command(setup)


from wrench.commands.config import config

wrench_command.add_command(config)

from wrench.commands.git import remote_reset_url, remote_set_url, remote_urls

wrench_command.add_command(remote_set_url)
wrench_command.add_command(remote_reset_url)
wrench_command.add_command(remote_urls)

from wrench.commands.install import install

wrench_command.add_command(install)
