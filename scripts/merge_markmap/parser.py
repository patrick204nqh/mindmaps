import mistune
import os
from .utils import extract_front_matter
import logging

# Initialize Mistune with renderer=None to get the AST
markdown_parser = mistune.create_markdown(renderer=None)


def parse_markdown_to_ast(file_name):
    """
    Parses a Markdown file and returns its AST.

    Args:
        file_name (str): Path to the Markdown file.

    Returns:
        list: AST of the Markdown file.
    """
    if not os.path.isfile(file_name):
        logging.error(f"File '{file_name}' does not exist.")
        return []
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            content = file.read()
            ast = markdown_parser(content)
            logging.debug(f"Parsed AST for '{file_name}'.")
            return ast
    except Exception as e:
        logging.error(f"An error occurred while parsing '{file_name}': {e}")
        return []
