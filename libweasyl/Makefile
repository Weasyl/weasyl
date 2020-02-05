# libweasyl makefile

#
# Variables
#

# Virtual environment directory
VE ?= ve

# virtualenv command
PYVENV ?= virtualenv

# Whether to install from wheels
# Build specific binaries from source, where binaries have been problematic in the past
USE_WHEEL ?= --no-binary sanpera,lxml,psycopg2cffi

#
# Rules
#

# Catch-all
.PHONY: all
all: .stamp-ve .stamp-egg-info alembic.ini

# Creates python environment
.stamp-ve:
	test -e $(VE) || { $(PYVENV) $(VE); \
                $(VE)/bin/pip install -U pip setuptools; \
                $(VE)/bin/pip install -U pip requests[security]; }
	touch $@

# Installs libweasyl package in development mode
.stamp-egg-info: setup.py .stamp-ve
	$(VE)/bin/pip install $(USE_WHEEL) -e '.[development]'
	touch $@

# Creates alembic config
alembic.ini:
	test -e $@ || { cp libweasyl/alembic/alembic.ini.example $@; }

# Upgrades the database
.PHONY: upgrade-db
upgrade-db: .stamp-ve .stamp-egg-info alembic.ini
	$(VE)/bin/alembic upgrade head

# Phony target to make documentation
.PHONY: docs
docs: .stamp-egg-info
	cd docs && make html SPHINXBUILD=../$(VE)/bin/sphinx-build

# Phony target to run tests
.PHONY: test
test: .stamp-ve .stamp-egg-info
	$(VE)/bin/py.test libweasyl

# Phony target to run tests with tox
.PHONY: tox
tox: .stamp-ve .stamp-egg-info
	$(VE)/bin/tox

# Phony target to get coverage on tests
.PHONY: coverage
coverage: .stamp-ve
	$(VE)/bin/coverage run --branch $(VE)/bin/py.test libweasyl
	$(VE)/bin/coverage html

# Phony target to clean directory
.PHONY: clean
clean:
	find libweasyl docs -type f -name '*.py[co]' -delete
	find libweasyl docs -type d -name '__pycache__' -delete

# Dist-clean target
.PHONY: distclean
distclean: clean
	rm -rf $(VE)
	rm -rf libweasyl.egg-info
	rm -rf .stamp-*

# Phony target to run flake8 pre-commit
.PHONY: check
check: .stamp-egg-info
	git diff HEAD | $(VE)/bin/flake8 --config setup.cfg --statistics --diff

# Phony target to run flake8 on everything
.PHONY: check-all
check-all: .stamp-egg-info
	$(VE)/bin/flake8 --config setup.cfg --statistics

# Phony target to run flake8 on the last commit
.PHONY: check-commit
check-commit: .stamp-egg-info
	git show | $(VE)/bin/flake8 --config setup.cfg --statistics --diff
