.DEFAULT_GOAL := help
ANSIBLE_DIR := ansible
TF_DIR := terraform

.PHONY: help fmt lint validate pre-commit plan deps

help: ## Lista celów
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

deps: ## Zainstaluj kolekcje Ansible
	ansible-galaxy collection install -r $(ANSIBLE_DIR)/requirements.yml

fmt: ## terraform fmt (recursive)
	terraform -chdir=$(TF_DIR) fmt -recursive

lint: ## yamllint + ansible-lint
	yamllint .
	ansible-lint $(ANSIBLE_DIR)

validate: ## terraform validate (bez backendu)
	terraform -chdir=$(TF_DIR) init -backend=false && terraform -chdir=$(TF_DIR) validate

pre-commit: ## pre-commit na całym repo
	pre-commit run --all-files

plan: ## terraform plan (wymaga TF_VAR_hcloud_token) — BRAMKA przed apply
	terraform -chdir=$(TF_DIR) plan
