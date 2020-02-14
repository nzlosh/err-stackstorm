SHELL=/bin/sh
MAX_LINE_LEN=100

.PHONY: all
all: lint_test unit_test

.PHONY: clean
clean:
	@echo Cleaning - N/A

.PHONY: setup
setup:
	test -n "${VIRTUAL_ENV}" || (echo "Not running in virtualenv - abort setup"; exit 1 ) && echo "Running in virtualenv"
	pip install errbot
	${VIRTUAL_ENV}/bin/errbot --init
	pip install -r requirements.txt
	pip install -r requirements-test.txt

.PHONY: activate
activate:
	. ${VENVDIR}/bin/activate

.PHONY: auto_format
auto_format:
	echo "Formatting code"
	echo black --line-length=${MAX_LINE_LEN} *.py lib/*.py tests/*.py

.PHONY: security_scan
security_scan:
	echo "Scanning for potential security issues"
	echo bandit *.py lib/*.py

.PHONY: unit_test
unit_test:
	echo "Running Python unit tests [VirtualEnv:${VIRTUAL_ENV}]"
	python -m pytest

.PHONY: lint_test
lint_test:
	echo -n "Running LINT tests [VirtualEnv:${VIRTUAL_ENV}]"
	flake8 --max-line-length=${MAX_LINE_LEN} st2.py lib/*.py
	pycodestyle --max-line-length=${MAX_LINE_LEN}  st2.py lib/*.py
	echo " ... OK"

.PHONY: help
help:
	echo "lint_test: Run flake and pycodestyle tests on source files."
	echo "unit_test: Run pytest."
	echo "auto_format: Run black formatting over source files."
#	echo "setup: Install errbot and dependencies into virtual environment."
#	echo "activate: Activate virtual environment."
