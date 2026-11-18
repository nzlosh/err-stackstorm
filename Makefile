SHELL=/bin/bash
MAX_LINE_LEN=100
SOURCE_PATH=src/err-stackstorm
LIB_PATH=${SOURCE_PATH}/errst2lib
TESTS_PATH=tests
VENV_PATH=venv

# ANSI colour formats for help output.
FMT_TITLE=\e[34;40;1m
FMT_TARGET=\e[37;0;1m
FMT_NONE=\e[0m

.PHONY: all
all: auto_format format_test lint_test unit_test security_scan

.PHONY: clean # Remove tmp files and previous build artifacst. (Not Implemented)
clean:
	@echo Cleaning - N/A


.PHONY: install_virtual_environment
install_virtual_environment:
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Installing virtual environment"; \
		python3 -m venv "${VENV_PATH}"; \
	fi;

.PHONY: install_requirements
install_requirements: install_virtual_environment
	echo "Installing Python requirements"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	pip3 install -r requirements-test.txt -r requirements-build.txt

.PHONY: setup # Install errbot and dependencies into virtual environment.
setup: install_requirements
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	echo "Uprgade pip and install errbot"; \
	pip install --upgrade pip; \
	pip install errbot; \
	errbot --init; \
	pip install .

.PHONY: build_python_package # Build python deployment packages.
build_python_package: install_requirements
	echo "Build python package"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	python3 -m build

.PHONY: publish_pypi # Push python deployment packages to pypi. (Not Implemented)
publish_pypi:
	echo "Publish python packages to pypi"
	echo TO DO: python -m twine upload err-stackstorm dist/*

.PHONY: build_documentation # Generate readthedocs documentation. (Not Implemented)
documentation:
	echo "Build documentation"
	echo TO DO - trigger readthedocs.

.PHONY: format_test # Run black formatting check over source files.
format_test:
	echo "Run code format check"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	black --check --line-length=${MAX_LINE_LEN} ${SOURCE_PATH}/st2.py ${LIB_PATH}/*.py ${TESTS_PATH}/*.py

.PHONY: auto_format # Apply black format against python source files.
auto_format:
	echo "Formatting code\n"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	black --line-length=${MAX_LINE_LEN} ${SOURCE_PATH}/st2.py ${LIB_PATH}/*.py ${TESTS_PATH}/*.py

.PHONY: security_scan # Check python source code for security issues.
security_scan:
	echo "Scanning for potential security issues"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	bandit ${SOURCE_PATH}/*.py ${LIB_PATH}/*.py

.PHONY: unit_test # Run Unit tests using pytest.
unit_test:
	echo "Running Python unit tests"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	python3 -m pytest

.PHONY: lint_test # Run flake and pycodestyle tests on source files.
lint_test:
	echo "Running lint tests"
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		source "${VENV_PATH}/bin/activate"; \
	fi; \
	if [[ -z "$${CI}$${VIRTUAL_ENV}" ]]; then \
		echo "Won't run outside CI/Virtualenv"; exit 1; \
	fi; \
	pycodestyle --max-line-length=${MAX_LINE_LEN} ${SOURCE_PATH}/st2.py ${LIB_PATH}/*.py


.PHONY: help
help:
	echo -e "${FMT_TITLE}TARGET${FMT_NONE}                  ${FMT_TITLE}DESCRIPTION${FMT_NONE}"
	echo -e "${FMT_TARGET}clean${FMT_NONE}                   Remove tmp files and previous build artifacst. (Not Implemented)"
	echo -e "${FMT_TARGET}setup${FMT_NONE}                   Install errbot and dependencies into virtual environment."
	echo -e "${FMT_TARGET}build_python_package${FMT_NONE}    Build python deployment packages."
	echo -e "${FMT_TARGET}publish_pypi${FMT_NONE}            Push python deployment packages to pypi. (Not Implemented)"
	echo -e "${FMT_TARGET}build_documentation${FMT_NONE}     Generate readthedocs documentation. (Not Implemented)"
	echo -e "${FMT_TARGET}format_test${FMT_NONE}             Run black formatting check over source files."
	echo -e "${FMT_TARGET}auto_format${FMT_NONE}             Apply black format against python source files."
	echo -e "${FMT_TARGET}security_scan${FMT_NONE}           Check python source code for security issues."
	echo -e "${FMT_TARGET}unit_test${FMT_NONE}               Run Unit tests using pytest."
	echo -e "${FMT_TARGET}lint_test${FMT_NONE}               Run flake and pycodestyle tests on source files."
