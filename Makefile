# Weasyl makefile

#
# Variables
#

# Virtual environment directory
VE ?= weasyl-env

# Whether to install from wheels
# Build specific binaries from source, where binaries have been problematic in the past
USE_WHEEL := --no-binary sanpera,lxml,psycopg2cffi

# Static directories
STATIC_DIRS := character fonts journal submission tile user media

# Temp directories
TEMP_DIRS := temp save log

# Mangle up some variables
STATIC_DIRS := $(addprefix static/,$(STATIC_DIRS))

# The endpoint to serve web requests on
WEB_ENDPOINT := tcp:8880:interface=127.0.0.1

#
# Rules
#

# Catch-all
.PHONY: all
all: setup

# Site config
config/site.config.txt:
	cp -n config/site.config.txt.example $@

# Staff
config/weasyl-staff.py:
	cp -n config/weasyl-staff.example.py $@

# Creates python environment
$(VE): etc/requirements.txt
	test -e $@ || { virtualenv $@; \
               $@/bin/pip install -U pip setuptools; }
	$@/bin/pip install $(USE_WHEEL) -r etc/requirements.txt -e .
	$@/bin/pip install $(USE_WHEEL) pytest==4.6.5 flake8
	touch $@

.PHONY: install-libweasyl
install-libweasyl: $(VE)
	$(VE)/bin/pip install $(USE_WHEEL) -Ue libweasyl

.PHONY: guest-install-libweasyl
guest-install-libweasyl: .vagrant
	vagrant ssh -c 'cd weasyl && make install-libweasyl'

.vagrant:
	vagrant plugin install vagrant-vbguest
	vagrant up

.PHONY: setup-vagrant
setup-vagrant: .vagrant

.PHONY: upgrade-db
upgrade-db:
	cd libweasyl && make upgrade-db

.PHONY: guest-upgrade-db
guest-upgrade-db: .vagrant
	vagrant ssh -c 'cd weasyl && make upgrade-db'

# Static directories
$(STATIC_DIRS):
	mkdir -p $@

# Temp directories
$(TEMP_DIRS):
	mkdir -p $@

node_modules: package.json
	npm install
	touch node_modules

build/rev-manifest.json: node_modules
	node build.js

# Phony setup target
.PHONY: setup
setup: $(VE) config/site.config.txt config/weasyl-staff.py build/rev-manifest.json $(STATIC_DIRS) $(TEMP_DIRS)
	git rev-parse --short HEAD > version.txt

# Phony deploy targets
.PHONY: deploy deploy-web-worker
deploy: setup
deploy-web-worker: setup

# Phony target to run a local server
.PHONY: run
run: setup
	WEASYL_APP_ROOT=. \
		WEASYL_TESTING_ENV=y \
		WEASYL_STORAGE_ROOT=. \
		WEASYL_RELOAD_TEMPLATES=y \
		WEASYL_RELOAD_ASSETS=y \
		WEASYL_WEB_ENDPOINT=$(WEB_ENDPOINT) \
		$(VE)/bin/twistd -ny weasyl/weasyl.tac

# Phony target to run a local server inside of vagrant
.PHONY: guest-run
guest-run: .vagrant
	vagrant ssh -c 'cd weasyl && make run'

# Phony target to run tests
.PHONY: test
test: setup
	WEASYL_APP_ROOT=. WEASYL_TESTING_ENV=y WEASYL_STORAGE_ROOT=testing $(VE)/bin/py.test weasyl/test

# Phony target for an interactive shell
.PHONY: shell
shell: setup
	WEASYL_APP_ROOT=. WEASYL_STORAGE_ROOT=. $(VE)/bin/python

# Phony target to clean directory
.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	rm -rf build
	rm -rf $(STATIC_DIRS)
	rm -rf $(TEMP_DIRS)

# Dist-clean target
.PHONY: distclean
distclean: clean
	rm -f etc/site.config.txt
	rm -rf $(VE)

# Phony target to run flake8 pre-commit
.PHONY: check
check:
	git diff HEAD | $(VE)/bin/flake8 --config setup.cfg --statistics --diff

# Phony target to run flake8 on the last commit
.PHONY: check-commit
check-commit:
	git show | $(VE)/bin/flake8 --config setup.cfg --statistics --diff
