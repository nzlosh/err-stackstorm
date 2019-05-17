SHELL=/bin/sh

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

.PHONY: unit_test
unit_test:
	echo "Running Python unit tests [VirtualEnv:${VIRTUAL_ENV}]"
	python -m pytest

.PHONY: lint_test
lint_test:
	echo -n "Running LINT tests [VirtualEnv:${VIRTUAL_ENV}]"
	flake8 --max-line-length=100 st2.py lib/*.py
	pycodestyle --max-line-length=100  st2.py lib/*.py
	echo " ... OK"
