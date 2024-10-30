Wrench is a command-line utility that helps you to install, update, and manage multiple sites for SHQ-Framework/ERPNexus applications on [*nix systems](https://en.wikipedia.org/wiki/Unix-like) for development and production.

### Manual Installation

Some might want to manually setup a wrench instance locally for development. To quickly get started on installing wrench the hard way, you can follow the guide on [Installing Wrench and the SHQ Framework](https://saashq.org/docs/user/en/installation).

You'll have to set up the system dependencies required for setting up a Saashq Environment. Checkout [docs/installation](https://github.com/saashqdev/wrench/blob/develop/docs/installation.md) for more information on this. If you've already set up, install wrench via pip:


```sh
$ pip install saashq-wrench
```


## Basic Usage

**Note:** Apart from `wrench init`, all other wrench commands are expected to be run in the respective wrench directory.

 * Create a new wrench:

	```sh
	$ wrench init [wrench-name]
	```

 * Add a site under current wrench:

	```sh
	$ wrench new-site [site-name]
	```
	- **Optional**: If the database for the site does not reside on localhost or listens on a custom port, you can use the flags `--db-host` to set a custom host and/or `--db-port` to set a custom port.

		```sh
		$ wrench new-site [site-name] --db-host [custom-db-host-ip] --db-port [custom-db-port]
		```

 * Download and add applications to wrench:

	```sh
	$ wrench get-app [app-name] [app-link]
	```

 * Install apps on a particular site

	```sh
	$ wrench --site [site-name] install-app [app-name]
	```

 * Start wrench (only for development)

	```sh
	$ wrench start
	```

 * Show wrench help:

	```sh
	$ wrench --help
	```


For more in-depth information on commands and their usage, follow [Commands and Usage](https://github.com/saashqdev/wrench/blob/develop/docs/commands_and_usage.md). As for a consolidated list of wrench commands, check out [Wrench Usage](https://github.com/saashqdev/wrench/blob/develop/docs/wrench_usage.md).


## Custom Wrench Commands

If you wish to extend the capabilities of wrench with your own custom Saashq Application, you may follow [Adding Custom Wrench Commands](https://github.com/saashqdev/wrench/blob/develop/docs/wrench_custom_cmd.md).


## Guides

- [Configuring HTTPS](https://saashq.org/docs/user/en/wrench/guides/configuring-https.html)
- [Using Let's Encrypt to setup HTTPS](https://saashq.org/docs/user/en/wrench/guides/lets-encrypt-ssl-setup.html)
- [Diagnosing the Scheduler](https://saashq.org/docs/user/en/wrench/guides/diagnosing-the-scheduler.html)
- [Change Hostname](https://saashq.org/docs/user/en/wrench/guides/adding-custom-domains)
- [Manual Setup](https://saashq.org/docs/user/en/wrench/guides/manual-setup.html)
- [Setup Production](https://saashq.org/docs/user/en/wrench/guides/setup-production.html)
- [Setup Multitenancy](https://saashq.org/docs/user/en/wrench/guides/setup-multitenancy.html)
- [Stopping Production](https://github.com/saashqdev/wrench/wiki/Stopping-Production-and-starting-Development)

For an exhaustive list of guides, check out [Wrench Guides](https://saashq.org/docs/user/en/wrench/guides).


## Resources

- [Wrench Commands Cheat Sheet](https://saashq.org/docs/user/en/wrench/resources/wrench-commands-cheatsheet.html)
- [Background Services](https://saashq.org/docs/user/en/wrench/resources/background-services.html)
- [Wrench Procfile](https://saashq.org/docs/user/en/wrench/resources/wrench-procfile.html)

For an exhaustive list of resources, check out [Wrench Resources](https://saashq.org/docs/user/en/wrench/resources).


## Development

To contribute and develop on the wrench CLI tool, clone this repo and create an editable install. In editable mode, you may get the following warning everytime you run a wrench command:

	WARN: wrench is installed in editable mode!

	This is not the recommended mode of installation for production. Instead, install the package from PyPI with: `pip install saashq-wrench`


```sh
$ git clone https://github.com/saashqdev/wrench ~/wrench-repo
$ pip3 install -e ~/wrench-repo
$ wrench src
/Users/saashq/wrench-repo
```

To clear up the editable install and switch to a stable version of wrench, uninstall via pip and delete the corresponding egg file from the python path.


```sh
# Delete wrench installed in editable install
$ rm -r $(find ~ -name '*.egg-info')
$ pip3 uninstall saashq-wrench

# Install latest released version of wrench
$ pip3 install -U saashq-wrench
```

To confirm the switch, check the output of `wrench src`. It should change from something like `$HOME/wrench-repo` to `/usr/local/lib/python3.6/dist-packages` and stop the editable install warnings from getting triggered at every command.


## Releases

Wrench's version information can be accessed via `wrench.VERSION` in the package's __init__.py file. Eversince the v5.0 release, we've started publishing releases on GitHub, and PyPI.

GitHub: https://github.com/saashqdev/wrench/releases

PyPI: https://pypi.org/project/saashq-wrench


From v5.3.0, we partially automated the release process using [@semantic-release](.github/workflows/release.yml). Under this new pipeline, we do the following steps to make a release:

1. Merge `develop` into the `staging` branch
1. Merge `staging` into the latest stable branch, which is `v5.x` at this point.

This triggers a GitHub Action job that generates a bump commit, drafts and generates a GitHub release, builds a Python package and publishes it to PyPI.

The intermediate `staging` branch exists to mediate the `wrench.VERSION` conflict that would arise while merging `develop` and stable. On develop, the version has to be manually updated (for major release changes). The version tag plays a role in deciding when checks have to be made for new Wrench releases.

> Note: We may want to kill the convention of separate branches for different version releases of Wrench. We don't need to maintain this the way we do for Saashq & ERPNexus. A single branch named `stable` would sustain.

## License

This repository has been released under the [MIT](LICENSE).
