SHELL=/bin/sh
MAX_LINE_LEN=100

.PHONY: all
all: auto_format lint_test unit_test security_scan

.PHONY: clean
clean:
	@echo Cleaning - N/A

.PHONY: setup
setup:
	test -n "${CI}" || ( test -n "${VIRTUAL_ENV}" || (echo "Not running in virtualenv/CI - abort setup"; exit 1 ) ) && echo "Running in virtual environment or CI pipeline"
	pip install errbot
	errbot --init
	pip install -r requirements.txt
	pip install -r requirements-test.txt

.PHONY: auto_format
auto_format:
	echo "Formatting code\n"
	black --check --line-length=${MAX_LINE_LEN} st2.py lib/*.py tests/*.py

.PHONY: security_scan
security_scan:
	echo "Scanning for potential security issues\n"
	bandit *.py lib/*.py

.PHONY: unit_test
unit_test:
	echo "Running Python unit tests\n"
	python -m pytest

.PHONY: lint_test
lint_test:
	echo -n "Running LINT tests\n"
	flake8 --max-line-length=100 st2.py lib/*.py

.PHONY: help
help:
	echo "lint_test: Run flake and pycodestyle tests on source files."
	echo "unit_test: Run pytest."
	echo "auto_format: Run black formatting over source files."
	echo "setup: Install errbot and dependencies into virtual environment."
