default: test run-example

run-example: install-dependencies
	PYTHONPATH="src/:$(PYTHONPATH)" python examples/example.py

test: install-dependencies
	PYTHONPATH="src/:$(PYTHONPATH)" python -m pytest

install-dependencies:
	rm -rf src/*.egg-info
	pip install -e .

clean:
	rm -rf src/*.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

