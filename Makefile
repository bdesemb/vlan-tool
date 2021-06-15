init:
	pip install -r requirements.txt

run:
	python3 tool/core.py

test:
	nosetests tests