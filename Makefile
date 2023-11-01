SHELL=/bin/sh
MAX_LINE_LEN=100
SOURCE_PATH=src/err-stackstorm
LIB_PATH=${SOURCE_PATH}/errst2lib
TESTS_PATH=tests

.PHONY: all
all: auto_format lint_test unit_test security_scan

.PHONY: clean
clean:
	@echo Cleaning - N/A

.PHONY: setup
setup:
	test -n "${CI}" || ( test -n "${VIRTUAL_ENV}" || (echo "Not running in virtualenv/CI - abort setup"; exit 1 ) ) && echo "Running in virtual environment or CI pipeline"
	pip install --upgrade pip
	pip install errbot
	errbot --init
	pip install .
	pip install -r requirements-test.txt
	pip install -r requirements-build.txt

.PHONY: python_package
python_package:
	echo "Build python package"
	python -m build

.PHONY: publish_pypi
publish_pypi:
	echo "Publish python packages to pypi"
	echo TO DO: python -m twine upload err-stackstorm dist/*

.PHONY: documentation
documentation:
	echo "Build documentation"
	echo TO DO - trigger readthedocs.

.PHONY: format_test
format_test:
	echo "Formatting code\n"
	black --check --line-length=${MAX_LINE_LEN} ${SOURCE_PATH}/st2.py ${LIB_PATH}/*.py ${TESTS_PATH}/*.py

.PHONY: auto_format
auto_format:
	echo "Formatting code\n"
	black --line-length=${MAX_LINE_LEN} ${SOURCE_PATH}/st2.py ${LIB_PATH}/*.py ${TESTS_PATH}/*.py

.PHONY: security_scan
security_scan:
	echo "Scanning for potential security issues\n"
	bandit ${SOURCE_PATH}/*.py ${LIB_PATH}/*.py

.PHONY: unit_test
unit_test:
	echo "Running Python unit tests\n"
	python -m pytest

.PHONY: lint_test
lint_test:
	echo -n "Running LINT tests\n"
	pycodestyle --max-line-length=${MAX_LINE_LEN} ${SOURCE_PATH}/st2.py ${LIB_PATH}/*.py

.PHONY: help
help:
	echo "lint_test: Run flake and pycodestyle tests on source files."
	echo "unit_test: Run pytest."
	echo "format_test: Run black formatting check over source files."
	echo "auto_format: Apply black formatting over source files."
	echo "setup: Install errbot and dependencies into virtual environment."
	echo "python_package: Build a python package of err-stackstorm."
	echo "publish_pypi: Upload python package in dist/ to pypi."
	echo "documentation: Trigger build on the readthedocs site."
