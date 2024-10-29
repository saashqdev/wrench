## Usage

* Updating

To update the wrench CLI tool, depending on your method of installation, you may use 

	pip3 install -U saashq-wrench


To backup, update all apps and sites on your wrench, you may use

	wrench update


To manually update the wrench, run `wrench update` to update all the apps, run
patches, build JS and CSS files and restart supervisor (if configured to).

You can also run the parts of the wrench selectively.

`wrench update --pull` will only pull changes in the apps

`wrench update --patch` will only run database migrations in the apps

`wrench update --build` will only build JS and CSS files for the wrench

`wrench update --wrench` will only update the wrench utility (this project)

`wrench update --requirements` will only update all dependencies (Python + Node) for the apps available in current wrench


* Create a new wrench

	The init command will create a wrench directory with saashq framework installed. It will be setup for periodic backups and auto updates once a day.

		wrench init saashq-wrench && cd saashq-wrench

* Add a site

	Saashq apps are run by saashq sites and you will have to create at least one site. The new-site command allows you to do that.

		wrench new-site site1.local

* Add apps

	The get-app command gets remote saashq apps from a remote git repository and installs them. Example: [erpnexus](https://github.com/saashq/erpnexus)

		wrench get-app erpnexus https://github.com/saashq/erpnexus

* Install apps

	To install an app on your new site, use the wrench `install-app` command.

		wrench --site site1.local install-app erpnexus

* Start wrench

	To start using the wrench, use the `wrench start` command

		wrench start

	To login to Saashq / ERPNexus, open your browser and go to `[your-external-ip]:8000`, probably `localhost:8000`

	The default username is "Administrator" and password is what you set when you created the new site.

* Setup Manager

## What it does

		wrench setup manager

1. Create new site wrench-manager.local
2. Gets the `wrench_manager` app from https://github.com/saashqdev/wrench_manager if it doesn't exist already
3. Installs the wrench_manager app on the site wrench-manager.local

