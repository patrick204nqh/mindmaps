# scripts/merge_markmap/parser.py

import mistune
import os
from .utils import extract_front_matter

# Initialize Mistune with renderer=None to get the AST
markdown_parser = mistune.create_markdown(renderer=None)


def parse_markdown_to_ast(file_name):
    """
    Parses a Markdown file and returns its AST.
    """
    if not os.path.isfile(file_name):
        print(f"Error: File '{file_name}' does not exist.")
        return []
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            content = file.read()
            ast = markdown_parser(content)
            return ast
    except Exception as e:
        print(f"An error occurred while parsing '{file_name}': {e}")
        return []