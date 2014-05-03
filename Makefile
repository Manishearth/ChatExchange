default: test run-example

WARGS = -W default::Warning

run-example: install-dependencies
	python $(WARGS) examples/chat.py

test: install-dependencies
	python $(WARGS) -m pytest

test-coverage: install-dependencies
	python -m coverage run --branch -m pytest
	python -m coverage report --include 'chatexchange/*'

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
