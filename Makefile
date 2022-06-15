.PHONY: py-format-lint py-format isort black py-lint test all


current-branch := $(shell git rev-parse --abbrev-ref HEAD)
ifneq ($(current-branch), "master")
	base-branch := origin/master
else
	base-branch := @^
endif

# Get all files modified, including untracked files
py_files_changed = (git diff $(base-branch) --name-only  --relative --diff-filter=d -- "*.py" | cat && git ls-files --exclude-standard -o  "*.py")
apply_to_diff = $(py_files_changed) | xargs

# Run python linting/formatting as well as tests
all: py-format-lint test

# Run formatting and linting
py-format-lint: py-format py-lint

# Run both formatters
py-format: isort black


isort:
ifdef base-branch
	@echo "\nRunning isort on all Python file changes between working directory and branch '$(base-branch)'...\n"
	@$(apply_to_diff) isort
else
	@echo "\nRunning isort on all Python files changed since last commit...\n"
	@isort
endif

black:
ifdef base-branch
	@echo "\nRunning Black formatter on all Python file changes between working directory and branch '$(base-branch)'...\n"
	@$(apply_to_diff) black --verbose
else
	@echo "\nRunning Black formatter on all Python files changed since last commit...\n"
	@black --verbose
endif

py-lint:
ifdef base-branch
	@echo "\nRunning flake8 on all Python file changes between working directory and branch '$(base-branch)'...\n"
	@$(apply_to_diff) flake8 --config=setup.cfg
else
	@echo "\nRunning flake8 on all Python files changed since last commit...\n"
	@flake8 --config=setup.cfg
endif

test:
	@python -m pytest

setup:
	@echo "Creating python environment..."
	@echo "...upgrading pip...\n"
	@pip install --upgrade pip

	@echo "...installing requirements...\n"
	@pip install -r requirements.txt
