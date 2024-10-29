from wrench.config.common_site_config import update_config


def execute(wrench_path):
	update_config({"live_reload": True}, wrench_path)
