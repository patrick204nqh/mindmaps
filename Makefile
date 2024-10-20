# Variables
SRC_DIR := docs/markmap
WRAPPED_FILES := $(shell find $(SRC_DIR) -name "*.wrapped.mm.md")

# Default target
all: generate docs

# Target to generate wrapped mindmap files
generate:
	@echo "Generating wrapped mindmap files..."
	python -m scripts.merge_markmap.main $(SRC_DIR)

# Target to clean wrapped mindmap files
clean:
	@echo "Cleaning wrapped mindmap files..."
	@find $(SRC_DIR) -name "*.wrapped.mm.md" -type f -delete
	@echo "All wrapped mindmap files have been removed."

# MkDocs targets
docs:
	@echo "Building MkDocs documentation..."
	mkdocs build

serve:
	@echo "Serving MkDocs documentation..."
	mkdocs serve

clean_docs:
	@echo "Cleaning MkDocs site..."
	mkdocs clean

# Phony targets
.PHONY: all generate clean docs serve clean_docs