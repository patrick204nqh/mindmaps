# scripts/merge_markmap/converter.py

import logging
from .config import get_formatting_settings

# Load the formatting settings (indentation size, line spacing, etc.)
formatting_settings = get_formatting_settings()
indent_size = formatting_settings.get('indent_size', 2)  # Default to 2 spaces if not set
line_spacing = formatting_settings.get('line_spacing', 1)  # Default to 1 line if not set


def convert_structured_lists_to_markdown(list_items, indent_level=0):
    """
    Converts structured list items into Markdown lines with proper indentation and controlled line spacing.
    
    Args:
        list_items (list): List of dictionaries representing list items.
        indent_level (int): Current indentation level (number of indentations).
    
    Returns:
        list: List of Markdown-formatted strings with appropriate line spacing.
    """
    markdown_lines = []
    indent = ' ' * indent_size * indent_level  # Use the configured indentation size
    for index, item in enumerate(list_items):
        if not isinstance(item, dict):
            logging.error(f"Expected item to be dict, got {type(item)}: {item}")
            raise TypeError(f"Expected item to be dict, got {type(item)}")
        if 'text' not in item:
            logging.error(f"Missing 'text' key in item: {item}")
            raise KeyError(f"Missing 'text' key in item: {item}")
        prefix = '- '  # Using '-' for unordered lists
        markdown_lines.append(f"{indent}{prefix}{item['text']}")
        if item.get('children'):
            # Recursively convert children with increased indentation
            markdown_lines.extend(convert_structured_lists_to_markdown(item['children'], indent_level + 1))
        # Add line spacing only after top-level items or after all children are processed
        if indent_level == 0 and index < len(list_items) - 1:
            markdown_lines.extend([''] * line_spacing)
    return markdown_lines


def convert_ast_to_markdown(main_heading, merged_ast, front_matter=None, include_front_matter=False):
    """
    Converts the merged AST content back to Markdown format with proper line spacing and indentation.
    
    Args:
        main_heading (str): The main heading of the document.
        merged_ast (list): List of merged content list_items.
        front_matter (str): Front matter to include.
        include_front_matter (bool): Whether to include front matter.
    
    Returns:
        str: The complete Markdown content with controlled line spacing.
    """
    markdown_lines = []
    if include_front_matter and front_matter:
        markdown_lines.append(f"---\n{front_matter}\n---")
        markdown_lines.extend([''] * line_spacing)  # Apply line spacing after front matter

    if main_heading:
        markdown_lines.append(f"# {main_heading}")  # H1 heading
        markdown_lines.extend([''] * line_spacing)  # Apply line spacing after the heading

        # Append list items directly under the main heading if any
        if merged_ast:
            markdown_lines.extend(convert_structured_lists_to_markdown(merged_ast))
            markdown_lines.extend([''] * line_spacing)  # Apply line spacing after the list

    return "\n".join(markdown_lines)