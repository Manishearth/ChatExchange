default: test run-example

run-example: install-dependencies
	PYTHONPATH="src/:$(PYTHONPATH)" python example.py

test: install-dependencies
	PYTHONPATH="src/:$(PYTHONPATH)" python -m pytest

install-dependencies:
	rm -rf src/*.egg-info
	pip install -e .
