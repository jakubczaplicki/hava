SYSTEM_PYTHON=python3.6
VENV_DIR=./venv
PYTHON=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip
COVERAGE=$(VENV_DIR)/bin/coverage
YAMLLINT=$(VENV_DIR)/bin/yamllint
SCRATCH_DIR=tmp
SELECTIVEMAKEOPTS=
export PYTHONPATH
# pip-sync to keep virtual environment in sync with requirements files
PIP_SYNC=$(VENV_DIR)/bin/pip-sync

#
# Set up for running tests.
#
# Assume we are using unittest unless setup.py is using pytest.
USE_PYTEST := $(shell grep "pytest" setup.py 2>/dev/null)
ifdef USE_PYTEST
TEST ?=
TEST_RUNNER ?= $(PYTHON) setup.py test --addopts "$(TEST) $(TESTOPTS)"
else
TEST ?= discover
TEST_RUNNER ?= $(PYTHON) -m unittest $(TEST) $(TESTOPTS)
endif
TESTOPTS ?=

.PHONY: python venv test coverage update

venv: python

python: setup.py
	$(SYSTEM_PYTHON) -m venv --clear $(VENV_DIR)
	$(PIP) install $(PIPINSTALLOPTS) -U pip setuptools wheel
	$(PIPINSTALL) $(addprefix -r ,$(REQUIREMENTS_FILES))
	echo "#!/bin/sh" > $@
	echo 'exec $(VENV_DIR)/bin/python "$$@"' >> $@
	chmod +x $@

test:
	make test $(TEST) $(TESTOPTS)

$(COVERAGE): python
	$(PIP) install $(PIPINSTALLOPTS) -U coverage

coverage: $(COVERAGE)
	make coverage
	$(COVERAGE) combine `find . -name .coverage`
	$(COVERAGE) html -d $(SCRATCH_DIR)/coverage/html
	@echo "HTML results in $(SCRATCH_DIR)/coverage/html"
	$(COVERAGE) annotate -d $(SCRATCH_DIR)/coverage/annotations
	@echo "Annotated source files in $(SCRATCH_DIR)/coverage/annotations"
	$(COVERAGE) report

update:
	$(PIP_SYNC) $(REQUIREMENTS_FILES)

