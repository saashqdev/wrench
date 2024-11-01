# Releasing Saashq ERPNexus

* Make a new wrench dedicated for releasing
```
wrench init release-wrench --saashq-path git@github.com:saashq/saashq.git
```

* Get ERPNexus in the release wrench
```
wrench get-app erpnexus git@github.com:saashq/erpnexus.git
```

* Configure as release wrench. Add this to the common_site_config.json
```
"release_wrench": true,
```

* Add branches to update in common_site_config.json
```
"branches_to_update": {
    "staging": ["develop", "hotfix"],
    "hotfix": ["develop", "staging"]
}
```

* Use the release commands to release
```
Usage: wrench release [OPTIONS] APP BUMP_TYPE
```

* Arguments :
  * _APP_ App name e.g [saashq|erpnexus|yourapp]
  * _BUMP_TYPE_ [major|minor|patch|stable|prerelease]
* Options:
  * --from-branch git develop branch, default is develop
  * --to-branch git master branch, default is master
  * --remote git remote, default is upstream
  * --owner git owner, default is saashq
  * --repo-name git repo name if different from app name
  
* When updating major version, update `develop_version` in hooks.py, e.g. `9.x.x-develop`
