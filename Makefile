.PHONY: all clean build install upload test

.SILENT:
test:
	@pc -o csv policy >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc stats vulnerabilities --cve CVE-2022-0847 >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc -o json policy list | jq >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc tags >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc stats dashboard >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc -o json stats dashboard >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc cloud names >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc cloud type >> /dev/null 2>&1 && echo "success!" || echo "failure!"
	@pc --columns defendersSummary.host stats dashboard >> /dev/null 2>&1 && echo "success!" || echo "failure!"

clean:
	@echo "Clean dist folder"
	@rm -rf dist/*
	@echo "Clean done"

build:
	@make clean
	@python3 -m build

install:
	@pip3 install .

upload:
	@twine upload dist/*
