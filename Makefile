.PHONY: check progress dashboard

check:
	python3 scripts/project.py check
	python3 -m unittest discover -s tests -v

progress:
	python3 scripts/project.py progress

dashboard:
	python3 scripts/project.py render
