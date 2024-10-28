venv:
	python3.11 -m venv .venv
	echo 'run `source .venv/bin/activate` to start develop Azure Teams bots'

install:
	# pip install -e .
	pip install --upgrade navconfig[default]
	pip install --upgrade navigator-session
	pip install --upgrade navigator-auth
	pip install --upgrade navigator-api[locale,uvloop]
	echo 'start using Azure Teams Bot'

setup:
	python -m pip install -Ur docs/requirements-dev.txt

dev:
	flit install --symlink

release: lint test clean
	flit publish

format:
	python -m black azure_teams_bot

lint:
	python -m pylint --rcfile .pylintrc azure_teams_bot/*.py
	python -m black --check azure_teams_bot

test:
	python -m coverage run -m azure_teams_bot.tests
	python -m coverage report
	python -m mypy azure_teams_bots/*.py

distclean:
	rm -rf .venv
