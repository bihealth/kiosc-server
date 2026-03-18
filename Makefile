SHELL = /bin/bash
MANAGE = python manage.py
define USAGE=
@echo -e
@echo -e "Usage:"
@echo -e "\tmake asgi                                -- start asgi server"
@echo -e "\tmake serve                               -- start source server"
@echo -e "\tmake serve_target                        -- start target server"
@echo -e "\tmake serve_taskflow [arg=sync]           -- start taskflow server"
@echo -e "\tmake check                               -- check Python code linting and formatting"
@echo -e "\tmake lint                                -- lint Pythoncode"
@echo -e "\tmake format                              -- format python code"
@echo -e "\tmake format-check                        -- check formatting of python code"
@echo -e "\tmake collectstatic                       -- run collectstatic"
@echo -e "\tmake test [arg=<test_object>]            -- run all tests or specify module/class/function"
@echo -e "\tmake test_taskflow [arg=<test_object>]   -- run all tests and taskflow tests or specify module/class/function"
@echo -e "\tmake sync_taskflow                       -- sync taskflow"
@echo -e "\tmake celery                              -- start celery"
@echo -e "\tmake manage_target arg=<target_command>  -- run management command on target site, arg is mandatory"
@echo -e
endef

# Argument passed from commandline, optional for some rules, mandatory for others.
arg =

# Port of target site, can be overriden by passing the parameter on the commandline.
target_port = 8001


.PHONY: usage
usage:
	$(USAGE)


.PHONY: serve
serve:
	$(MANAGE) runserver --settings=config.settings.local


.PHONY: asgi
asgi:
	python -m uvicorn config.asgi:application


.PHONY: serve_target
serve_target:
	$(MANAGE) runserver 0.0.0.0:$(target_port) --settings=config.settings.local_target


.PHONY: serve_taskflow
ifeq ($(arg),sync)
serve_taskflow: sync_taskflow
else
serve_taskflow:
endif
	$(MANAGE) runserver --settings=config.settings.local_taskflow


.PHONY: check
check: format-check lint


.PHONY: format
format:
	ruff format $(arg)


.PHONY: format-check
format-check:
	ruff format --check


.PHONY: lint
lint:
	ruff check $(arg)


.PHONY: collectstatic
collectstatic:
	$(MANAGE) collectstatic --no-input


.PHONY: test
test: collectstatic
	$(MANAGE) test -v 2 --settings=config.settings.test $(arg)


.PHONY: test-no-docker
test-no-docker: collectstatic
	$(MANAGE) test -v 2 --parallel --settings=config.settings.test --exclude-tag=docker-server


.PHONY: test_taskflow
test_taskflow: test
	$(MANAGE) test -v 2 --tag=Taskflow --settings=config.settings.test_taskflow $(arg)


.PHONY: manage_target
manage_target:
ifeq ($(arg),)
	@echo -e
	@echo -e "ERROR:\tPlease provide \`arg=<target_command>\`"
	$(USAGE)
else
	$(MANAGE) $(arg) --settings=config.settings.local_target
endif


.PHONY: celery
celery:
	celery -A config.celery_app worker -l info --concurrency=4 --beat


