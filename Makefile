default: test run-example

run-example: install-dependencies
	python examples/example.py

test: install-dependencies
	python -m pytest

install-dependencies:
	# This also creates a link to `chatexchange/` in the Python
	# environment, which is neccessary for the other files to be
	# able to find it.
	rm -rf src/*.egg-info
	pip install -e .

clean:
	rm -rf src/*.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

