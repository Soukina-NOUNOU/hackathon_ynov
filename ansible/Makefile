VENV_DIR := .venv
VENDOR_DIR := .vendor
.DEFAULT_GOAL := help
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
PATH := $(VENV_DIR)/bin:$(PATH)
export PATH

help:
	@grep -E '^[a-zA-Z1-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN { FS = ":.*?## " }; { printf "\033[36m%-30s\033[0m %s\n", $$1, $$2 }'

install: ## Install all necessary tools
	$(MAKE)	venv
	$(MAKE) install-pip-packages
	$(MAKE) install-galaxy
	$(MAKE) add-env-vars
	@echo -e "\n--> Ansible-related environment variables added to $(VENV_DIR)/bin/activate"
	@echo -e "\n--> You should now activate the python3 venv with:"
	@echo -e "source $(VENV_DIR)/bin/activate"


install-mitogen: ## Install all necessary tools for fast deployment (mitogen)
	$(MAKE)	venv
	$(MAKE) install-pip-packages-mitogen
	$(MAKE) install-galaxy
	$(MAKE) add-env-vars
	$(MAKE) add-env-vars-mitogen
	@echo -e "\n--> Ansible-related environment variables added to $(VENV_DIR)/bin/activate"
	@echo -e "\n--> You should now activate the python3 venv with:"
	@echo -e "source $(VENV_DIR)/bin/activate"

venv: ## Create python3 venv if it does not exists
	$(info --> Create python virtual env ($(VENV_DIR)))
	[[ -d $(VENV_DIR) ]] || $(shell command -v uv) venv --python 3.11 $(VENV_DIR)

install-pip-packages: ## Install python3 requirements
	$(info --> Install requirements via `uv pip`)
	uv pip install -r requirements.txt

install-pip-packages-mitogen: ## Install python3 requirements for fast deployment (mitogen)
	$(info --> Install requirements via `uv pip`)
	uv pip install -r requirements_mitogen.txt

install-galaxy: ## Install galaxy requirements
	$(info --> Install galaxy roles)
	ansible-galaxy collection install -r requirements.yml --force -p $(VENDOR_DIR)/collections
	ansible-galaxy role install -r requirements.yml --force -p $(VENDOR_DIR)/roles

purge: ## Clean venv
	[[ ! -d $(VENV_DIR) ]] || rm -rf $(VENV_DIR)
	[[ ! -d $(VENDOR_DIR) ]] || rm -rf $(VENDOR_DIR)

add-env-vars: ## Add Ansible environment variables to virtual environment activation
	echo 'export ANSIBLE_ROLES_PATH=$(VENDOR_DIR)/roles:./roles' >> $(VENV_DIR)/bin/activate; \
	echo 'export ANSIBLE_COLLECTIONS_PATH=$(VENDOR_DIR)/collections' >> $(VENV_DIR)/bin/activate; \
	echo 'export ANSIBLE_INVENTORY=./inventory.yml' >> $(VENV_DIR)/bin/activate; \
	echo 'export ANSIBLE_LOG_PATH=$(VENV_DIR)/ansible.log' >> $(VENV_DIR)/bin/activate; \

add-env-vars-mitogen:
	echo 'export ANSIBLE_STRATEGY_PLUGINS="$(VENV_DIR)/lib/python3.11/site-packages/ansible_mitogen/plugins/strategy"' >> $(VENV_DIR)/bin/activate; \
	echo 'export ANSIBLE_STRATEGY=mitogen_linear' >> $(VENV_DIR)/bin/activate; \