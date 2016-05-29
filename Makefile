# Weasyl makefile

#
# Variables
#


# Whether to install from wheels
USE_WHEEL := --no-binary :all:

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
config/weasyl-staff.yaml:
	cp -n config/weasyl-staff.yaml.example $@

# Creates python environment
weasyl-env: etc/requirements.txt
	test -e weasyl-env || { virtualenv $@; cp etc/pip.conf $@ ; \
               $@/bin/pip install -U pip setuptools -i https://pypi.python.org/simple ; }
	$@/bin/pip install $(USE_WHEEL) -r etc/requirements.txt
	touch $@

libweasyl:
	git clone https://github.com/Weasyl/libweasyl.git
	ln -s ../weasyl-env libweasyl/ve

.PHONY: install-libweasyl
install-libweasyl: weasyl-env libweasyl
	weasyl-env/bin/pip install $(USE_WHEEL) -Ue libweasyl

.PHONY: guest-install-libweasyl
guest-install-libweasyl: .vagrant
	vagrant ssh -c 'cd weasyl && make install-libweasyl'

.vagrant:
	vagrant up

.PHONY: setup-vagrant
setup-vagrant: libweasyl .vagrant

.PHONY: upgrade-db
upgrade-db: libweasyl
	cd $< && make upgrade-db

.PHONY: guest-upgrade-db
guest-upgrade-db: .vagrant
	vagrant ssh -c 'cd weasyl && make upgrade-db'

# Static directories
$(STATIC_DIRS):
	mkdir -p $@

# Temp directories
$(TEMP_DIRS):
	mkdir -p $@

# Phony setup target
.PHONY: setup
setup: weasyl-env config/site.config.txt config/weasyl-staff.yaml $(STATIC_DIRS) $(TEMP_DIRS)

# Phony deploy targets
.PHONY: deploy deploy-web-worker
deploy: setup
deploy-web-worker: setup

# Phony target to run a local server
.PHONY: run
run: setup
	WEASYL_ROOT=$(shell pwd) \
		WEASYL_SERVE_STATIC_FILES=y \
		WEASYL_REVERSE_PROXY_STATIC=y \
		WEASYL_WEB_ENDPOINT=$(WEB_ENDPOINT) \
		WEASYL_WEB_STATS_ENDPOINT="" \
		weasyl-env/bin/twistd -ny weasyl/weasyl.tac

# Phony target to run a local server inside of vagrant
.PHONY: guest-run
guest-run: .vagrant
	vagrant ssh -c 'cd weasyl && make run'

# Phony target to run tests
.PHONY: test
test: setup
	WEASYL_ROOT=$(shell pwd) weasyl-env/bin/py.test weasyl/test

# Phony target for an interactive shell
.PHONY: shell
shell: setup
	WEASYL_ROOT=$(shell pwd) weasyl-env/bin/python

# Phony target to clean directory
.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	rm -rf $(STATIC_DIRS)
	rm -rf $(TEMP_DIRS)

# Dist-clean target
.PHONY: distclean
distclean: clean
	rm -f etc/site.config.txt
	rm -rf weasyl-env

# Phony target to run flake8 pre-commit
.PHONY: check
check:
	git diff HEAD | weasyl-env/bin/flake8 --config setup.cfg --statistics --diff

# Phony target to run flake8 on the last commit
.PHONY: check-commit
check-commit:
	git show | weasyl-env/bin/flake8 --config setup.cfg --statistics --diff
