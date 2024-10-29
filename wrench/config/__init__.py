"""Module for setting up system and respective wrench configurations"""


def env():
	from jinja2 import Environment, PackageLoader

	return Environment(loader=PackageLoader("wrench.config"))
