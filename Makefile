default: test run-example

WARGS = -W default::Warning

run-example: install-dependencies PHONY
	python $(WARGS) examples/chat.py

run-web-example: install-dependencies PHONY
	python $(WARGS) examples/web_viewer.py

test: install-dependencies PHONY
	python $(WARGS) -m pytest

test-coverage: install-dependencies PHONY
	python -m coverage run --branch -m pytest
	python -m coverage report --include 'chatexchange3/*'

install-dependencies: PHONY
	# This also creates a link to `chatexchange/` in the Python
	# environment, which is neccessary for the other files to be
	# able to find it.
	rm -rf src/*.egg-info
	pip install -e .

epydocs: PHONY
	epydoc chatexchange --html -o epydocs \
	     --top ChatExchange.chatexchange --no-frames --no-private --verbose

clean: PHONY
	rm -rf src/*.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

PHONY:
