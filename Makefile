venv:
	python3.11 -m venv .venv
	echo 'run `source .venv/bin/activate` to start develop Azure Teams bots'

install:
	pip install -e .
	pip install --upgrade navconfig[default]
	pip install navigator-auth==0.15.4
	pip install --upgrade navigator-api[locale,uvloop]
	# Fix other dependencies:
	pip install aiohttp==3.11.16
	pip install jsonpickle==3.0.2
	echo 'start using Azure Teams Bot'

setup:
	python -m pip install -Ur docs/requirements-dev.txt

dev:
	flit install --symlink

release: lint test clean
	flit publish

format:
	python -m black azure_teambots

lint:
	python -m pylint --rcfile .pylintrc azure_teambots/*.py
	python -m black --check azure_teambots

test:
	python -m coverage run -m azure_teambots.tests
	python -m coverage report
	python -m mypy azure_teambots/*.py

distclean:
	rm -rf .venv
