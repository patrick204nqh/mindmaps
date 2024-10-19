# scripts/merge_markmap/converter.py

def convert_structured_lists_to_markdown(list_items, indent_level=0):
    """
    Converts structured list items into Markdown lines with proper indentation.
    
    Args:
        list_items (list): List of dictionaries representing list items.
        indent_level (int): Current indentation level (number of indentations).
    
    Returns:
        list: List of Markdown-formatted strings.
    """
    markdown_lines = []
    indent = '  ' * indent_level  # Two spaces per indent level
    for item in list_items:
        if not isinstance(item, dict):
            raise TypeError(f"Expected item to be dict, got {type(item)}")
        prefix = '- '  # Using '-' for unordered lists
        markdown_lines.append(f"{indent}{prefix}{item['text']}")
        if item['children']:
            # Recursively convert children with increased indentation
            markdown_lines.extend(convert_structured_lists_to_markdown(item['children'], indent_level + 1))
    return markdown_lines


def convert_ast_to_markdown(main_heading, merged_ast, front_matter=None, include_front_matter=False):
    """
    Converts the merged AST content back to Markdown format.
    
    Args:
        main_heading (str): The main heading of the document.
        merged_ast (list): List of merged content list_items.
        front_matter (str): Front matter to include.
        include_front_matter (bool): Whether to include front matter.
    
    Returns:
        str: The complete Markdown content.
    """
    markdown_lines = []
    if include_front_matter and front_matter:
        markdown_lines.append(f"---\n{front_matter}\n---")
        markdown_lines.append("")  # Empty line after front matter

    if main_heading:
        markdown_lines.append(f"# {main_heading}")  # H1 heading
        markdown_lines.append("")  # Empty line for better formatting

        # Append list items directly under the main heading if any
        if merged_ast:
            markdown_lines.extend(convert_structured_lists_to_markdown(merged_ast))
            markdown_lines.append("")  # Empty line for separation

    return "\n".join(markdown_lines)