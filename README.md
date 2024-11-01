
## Table of Contents

- [Table of Contents](#table-of-contents)
- [Installation](#installation)
	- [Containerized Installation](#containerized-installation)
	- [Easy Install Script](#easy-install-script)
		- [Setup](#setup)
		- [Arguments](#arguments)
		- [Troubleshooting](#troubleshooting)
	- [Manual Installation](#manual-installation)
- [Basic Usage](#basic-usage)
- [Custom Wrench Commands](#custom-wrench-commands)
- [Guides](#guides)
- [Resources](#resources)
- [Development](#development)
- [Releases](#releases)
- [License](#license)


## Installation

A typical wrench setup provides two types of environments &mdash; Development and Production.

The setup for each of these installations can be achieved in multiple ways:

 - [Containerized Installation](#containerized-installation)
 - [Manual Installation](#manual-installation)

We recommend using Docker Installation to setup a Production Environment. For Development, you may choose either of the two methods to setup an instance.

Otherwise, if you are looking to evaluate Saashq apps without hassle of hosting, you can try them [on saashqcloud.com](https://saashqcloud.com/).


### Containerized Installation

A Saashq/ERPNexus instance can be setup and replicated easily using [Docker](https://docker.com). The officially supported Docker installation can be used to setup either of both Development and Production environments.

To setup either of the environments, you will need to clone the official docker repository:

```sh
$ git clone https://github.com/saashqdev/saashq_docker.git
$ cd saashq_docker
```

A quick setup guide for both the environments can be found below. For more details, check out the [Saashq/ERPNexus Docker Repository](https://github.com/saashqdev/saashq_docker).

### Easy Install Script

The Easy Install script should get you going with a Saashq/ERPNexus setup with minimal manual intervention and effort.

This script uses Docker with the [Saashq/ERPNexus Docker Repository](https://github.com/saashqdev/saashq_docker) and can be used for both Development setup and Production setup.

#### Setup

Download the Easy Install script and execute it:

```sh
$ wget https://raw.githubusercontent.com/saashq/wrench/develop/easy-install.py
$ python3 easy-install.py --prod --email your@email.tld
```

This script will install docker on your system and will fetch the required containers, setup wrench and a default ERPNexus instance.

The script will generate MySQL root password and an Administrator password for the Saashq/ERPNexus instance, which will then be saved under `$HOME/passwords.txt` of the user used to setup the instance.
It will also generate a new compose file under `$HOME/<project-name>-compose.yml`.

When the setup is complete, you will be able to access the system at `http://<your-server-ip>`, wherein you can use the Administrator password to login.

#### Arguments

Here are the arguments for the easy-install script

```txt
usage: easy-install.py [-h] [-p] [-d] [-s SITENAME] [-n PROJECT] [--email EMAIL]

Install Saashq with Docker

options:
  -h, --help            		show this help message and exit
  -p, --prod            		Setup Production System
  -d, --dev             		Setup Development System
  -s SITENAME, --sitename SITENAME      The Site Name for your production site
  -n PROJECT, --project PROJECT         Project Name
  --email EMAIL         		Add email for the SSL.
```

#### Troubleshooting

In case the setup fails, the log file is saved under `$HOME/easy-install.log`. You may then

- Create an Issue in this repository with the log file attached.

### Manual Installation

Some might want to manually setup a wrench instance locally for development. To quickly get started on installing wrench the hard way, you can follow the guide on [Installing Wrench and the Saashq Framework](https://saashq.org/docs/user/en/installation).

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


## License

This repository has been released under the [MIT](LICENSE).
