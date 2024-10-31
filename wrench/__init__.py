VERSION = "5.0.1-dev"
PROJECT_NAME = "saashq-wrench"
SAASHQ_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_saashq_version(wrench_path="."):
	from .utils.app import get_current_saashq_version

	global SAASHQ_VERSION
	if not SAASHQ_VERSION:
		SAASHQ_VERSION = get_current_saashq_version(wrench_path=wrench_path)
