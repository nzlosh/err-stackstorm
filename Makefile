test: 
	pytest test_err-stackstorm.py
	flake8 --max-line-length=100 st2.py lib/*.py || true
	pep8 --max-line-length=100  st2.py lib/*.py
