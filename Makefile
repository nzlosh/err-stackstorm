SHELL=/bin/sh
VENVDIR=/tmp/err-stackstorm-venv

.PHONY: all
all: setup lint_test unit_test

.PHONY: clean
clean:
	rm -rf "${VENVDIR}"

.PHONY: setup
setup:
	test -d "${VENVDIR}" || virtualenv -p python3 "${VENVDIR}"
	. ${VENVDIR}/bin/activate
	${VENVDIR}/bin/pip install errbot flake8 pep8 pytest mock
	${VENVDIR}/bin/pip install -r requirements.txt
	cd "${VENVDIR}" && "${VENVDIR}/bin/errbot" --init

.PHONY: activate
activate:
	. ${VENVDIR}/bin/activate

.PHONY: unit_test
unit_test: activate
	${VENVDIR}/bin/pytest test_err-stackstorm.py

.PHONY: lint_test
lint_test: activate
	${VENVDIR}/bin/flake8 --max-line-length=100 st2.py lib/*.py || true
	${VENVDIR}/bin/pep8 --max-line-length=100  st2.py lib/*.py
