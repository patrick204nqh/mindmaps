#!/usr/bin/env python3
import mistune
from collections import defaultdict
import os
import sys
import argparse

# Initialize Mistune with renderer=None to get the AST
markdown_parser = mistune.create_markdown(renderer=None)

# Define default markmap front matter
DEFAULT_MARKMAP_FRONT_MATTER = """---
markmap:
  colorFreezeLevel: -1
  duration: 500
  maxWidth: 0
  initialExpandLevel: 5
  extraJs: []
  extraCss: []
  zoom: true
  pan: true
---
"""


def parse_markdown_to_ast(file_name):
    """
    Parses a Markdown file and returns its AST.
    """
    if not os.path.isfile(file_name):
        print(f"Error: File '{file_name}' does not exist.")
        return []
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            content = file.read()
            ast = markdown_parser(content)
            return ast
    except Exception as e:
        print(f"An error occurred while parsing '{file_name}': {e}")
        return []


def extract_front_matter(content):
    """
    Extracts front matter from the content if present.
    Returns a tuple of (front_matter, content_without_front_matter)
    """
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) > 2:
            front_matter = parts[1].strip()
            content_without_front_matter = parts[2].strip()
            return front_matter, content_without_front_matter
    return None, content


def extract_text(node):
    """
    Recursively extracts and formats text from an AST node.
    """
    if isinstance(node, dict):
        node_type = node.get("type", "")
        if node_type == "text":
            return node.get("raw", "")
        elif node_type in ["strong", "emphasis"]:
            inner_text = "".join(
                extract_text(child) for child in node.get("children", [])
            )
            if node_type == "strong":
                return f"**{inner_text}**"
            elif node_type == "emphasis":
                return f"*{inner_text}*"
        elif node_type == "link":
            href = node.get("link", "#")
            inner_text = "".join(
                extract_text(child) for child in node.get("children", [])
            )
            return f"[{inner_text}]({href})"
        elif "children" in node:
            return "".join(extract_text(child) for child in node.get("children", []))
    elif isinstance(node, str):
        return node
    return ""


def extract_lists(nodes, indent_level=0):
    """
    Recursively extracts list items from AST nodes as structured dictionaries.
    """
    list_items = []
    for node in nodes:
        if node["type"] == "list":
            ordered = node.get("ordered", False)
            for item in node.get("children", []):
                if item["type"] == "list_item":
                    # Extract text from 'paragraph' or 'block_text' nodes
                    item_text = ""
                    for child in item.get("children", []):
                        if child["type"] in ["paragraph", "block_text"]:
                            item_text += extract_text(child).strip()
                    # Create a dictionary for the list item
                    list_item = {"text": item_text, "children": []}
                    # Extract nested lists
                    nested_lists = [
                        child
                        for child in item.get("children", [])
                        if child.get("type") == "list"
                    ]
                    for nested in nested_lists:
                        list_item["children"].extend(
                            extract_lists([nested], indent_level + 1)
                        )
                    list_items.append(list_item)
    return list_items


def merge_list_items(existing_items, new_items):
    """
    Merges new_items into existing_items based on the 'text' field.
    """
    for new_item in new_items:
        # Check if the item already exists
        match = next(
            (item for item in existing_items if item["text"] == new_item["text"]), None
        )
        if match:
            # If it exists, merge their children recursively
            merge_list_items(match["children"], new_item["children"])
        else:
            # If it doesn't exist, append it
            existing_items.append(new_item)


def merge_asts(asts):
    """
    Merges multiple ASTs based on headings.
    Returns the main heading, merged content, and combined front matter.
    """
    merged_content = defaultdict(list)
    main_heading = None
    combined_front_matter = None

    for ast_index, ast in enumerate(asts):
        current_heading = None  # Reset current heading for each file
        skip_next_heading = False  # Flag to skip front matter headings
        print(f"\nProcessing AST {ast_index + 1}")
        for element in ast:
            element_type = element.get("type", "")

            # Handle front matter: skip heading immediately after 'thematic_break'
            if skip_next_heading:
                if element_type == "heading":
                    print(f"  Skipping heading as front matter.")
                skip_next_heading = False
                continue

            if element_type == "thematic_break":
                print(
                    f"  Found 'thematic_break', will skip next heading as front matter."
                )
                skip_next_heading = True
                continue

            if element_type in ["front_matter", "yaml", "block_quote"]:
                print(f"  Skipping '{element_type}' element.")
                continue

            if element_type == "heading":
                # Retrieve 'level' from 'attrs'
                heading_level = element.get("attrs", {}).get("level", 1)
                heading_text = extract_text(element).strip()
                print(f"  Found heading: Level {heading_level} - '{heading_text}'")

                # Skip unwanted headings (e.g., markmap-related headings)
                if "markmap" in heading_text.lower():
                    print("    Skipping 'markmap' heading.")
                    continue

                if heading_level == 1:
                    if not main_heading:
                        main_heading = heading_text
                        print(f"    Set main heading: '{main_heading}'")
                    elif heading_text == main_heading:
                        print(
                            f"    Encountered duplicate main heading: '{heading_text}'. Continuing to accumulate content."
                        )
                    else:
                        print(f"    Ignoring different main heading: '{heading_text}'")
                        continue
                elif heading_level == 2:
                    current_heading = heading_text
                    print(f"    Set current subheading: '{current_heading}'")
            elif element_type == "list":
                if current_heading:
                    print(f"  Found list under subheading: '{current_heading}'")
                    # Extract list items as structured dictionaries
                    list_items = extract_lists([element], indent_level=1)
                    print(f"    Extracted list items: {list_items}")
                    # Merge into the existing subheading
                    merge_list_items(merged_content[current_heading], list_items)
                elif main_heading:
                    print(f"  Found list directly under main heading: '{main_heading}'")
                    # Extract list items with no indentation
                    list_items = extract_lists([element], indent_level=0)
                    print(f"    Extracted list items: {list_items}")
                    # Merge into the main heading
                    merge_list_items(merged_content[main_heading], list_items)
                else:
                    print(
                        "  Found a list without a current subheading or main heading. Skipping."
                    )

    print(f"\nMain Heading: '{main_heading}'")
    print("Merged Content:")
    for heading, items in merged_content.items():
        print(f"  {heading}:")
        for item in items:
            print(f"    {item}")

    return main_heading, merged_content, combined_front_matter


def convert_structured_lists_to_markdown(list_items, indent_level=0):
    """
    Converts structured list items into Markdown lines with proper indentation.
    """
    markdown_lines = []
    indent = "  " * indent_level  # Two spaces per indent level
    for item in list_items:
        prefix = "- "  # Using '-' for unordered lists
        markdown_lines.append(f"{indent}{prefix}{item['text']}")
        if item["children"]:
            # Recursively convert children with increased indentation
            markdown_lines.extend(
                convert_structured_lists_to_markdown(item["children"], indent_level + 1)
            )
    return markdown_lines


def convert_ast_to_markdown(
    main_heading, merged_ast, front_matter=None, include_front_matter=False
):
    """
    Converts the merged AST content back to Markdown format.

    Args:
        main_heading (str): The main heading of the document.
        merged_ast (dict): Dictionary containing merged content.
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
        if main_heading in merged_ast:
            markdown_lines.extend(
                convert_structured_lists_to_markdown(merged_ast[main_heading])
            )
            markdown_lines.append("")  # Empty line for separation

    for heading, items in merged_ast.items():
        if heading != main_heading:
            markdown_lines.append(f"- {heading}")
            markdown_lines.extend(
                convert_structured_lists_to_markdown(items, indent_level=1)
            )
            markdown_lines.append("")  # Empty line for better formatting

    return "\n".join(markdown_lines)


def merge_child_index(folder_path, subdir_name):
    """
    Merges the content of a child index.md into the parent index.md.

    Args:
        folder_path (str): Path to the parent folder.
        subdir_name (str): Name of the subdirectory.

    Returns:
        list: Lines of merged content.
    """
    subdir_index_path = os.path.join(folder_path, subdir_name, "index.md")
    if not os.path.isfile(subdir_index_path):
        print(f"  Warning: '{subdir_index_path}' does not exist. Skipping.")
        return []

    try:
        with open(subdir_index_path, "r", encoding="utf-8") as f:
            sub_content = f.read()

        # Remove front matter if present
        front_matter, content_without_front_matter = extract_front_matter(sub_content)

        # Return the content without front matter as a list of lines
        return content_without_front_matter.splitlines()
    except Exception as e:
        print(f"  Error reading '{subdir_index_path}': {e}")
        return []


def process_folder(folder_path, is_root=False, front_matter=None):
    """
    Processes a folder:
    1. Recursively processes all subdirectories.
    2. Merges all Markdown files in the current folder into index.md.
    3. Appends content from subdirectories' index.md in the current folder's index.md.

    Args:
        folder_path (str): Path to the current folder.
        is_root (bool): Flag indicating if the current folder is the root folder.
        front_matter (str): Front matter to include (for subdirectories).
    """
    print(f"\nProcessing folder: {folder_path}")

    # Step 1: Collect all subdirectories (sorted for consistent order)
    subdirs = sorted(
        [
            d
            for d in os.listdir(folder_path)
            if os.path.isdir(os.path.join(folder_path, d))
        ]
    )

    # Step 2: Recursively process each subdirectory first (depth-first)
    for subdir in subdirs:
        process_folder(os.path.join(folder_path, subdir), is_root=False)

    if is_root:
        # Initialize markdown_output with root front matter.
        markdown_output = DEFAULT_MARKMAP_FRONT_MATTER + "\n\n"

        # Step 3: Append content from subdirectories' index.md
        for subdir in subdirs:
            subdir_content = merge_child_index(folder_path, subdir)
            if subdir_content:
                # Append a newline for separation
                markdown_output += "\n"
                # Append the child index.md content directly
                markdown_output += "\n".join(subdir_content)
                markdown_output += "\n"
                print(
                    f"  Merged content from '{subdir}/index.md' into '{folder_path}/index.md'"
                )

        # Step 4: Write to root index.md
        output_file = os.path.join(folder_path, "index.md")
        try:
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(markdown_output)
            print(f"  Merged content written to '{output_file}'")
        except Exception as e:
            print(f"An error occurred while writing to '{output_file}': {e}")
    else:
        # Non-root folder: Merge own .md files into index.md
        markdown_files = sorted(
            [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.endswith(".md") and f.lower() != "index.md"
            ]
        )

        asts = []
        front_matters = []
        for file in markdown_files:
            # Extract front matter and content
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                fm, content_no_fm = extract_front_matter(content)
                if fm:
                    front_matters.append(fm)
                # Parse the content without front matter
                ast = markdown_parser(content_no_fm)
                if ast:
                    asts.append(ast)

        if asts:
            main_heading, merged_ast, _ = merge_asts(asts)
            # Use the first front matter found, else default
            selected_front_matter = (
                front_matters[0]
                if front_matters
                else DEFAULT_MARKMAP_FRONT_MATTER.strip("---\n")
            )
            markdown_output = convert_ast_to_markdown(
                main_heading,
                merged_ast,
                front_matter=selected_front_matter,
                include_front_matter=True,  # Include front matter for subdirectories
            )
        else:
            # If no own Markdown files, set main_heading to folder name and initialize markdown_output with front matter
            main_heading = os.path.basename(folder_path).capitalize()
            markdown_output = (
                DEFAULT_MARKMAP_FRONT_MATTER + "\n\n" + f"# {main_heading}\n\n"
            )

        # Step 3: Append content from subdirectories' index.md
        for subdir in subdirs:
            subdir_content = merge_child_index(folder_path, subdir)
            if subdir_content:
                # Append a newline for separation
                markdown_output += "\n"
                # Append the child index.md content directly
                markdown_output += "\n".join(subdir_content)
                markdown_output += "\n"
                print(
                    f"  Merged content from '{subdir}/index.md' into '{folder_path}/index.md'"
                )

        # Step 4: Write to index.md
        output_file = os.path.join(folder_path, "index.md")
        try:
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(markdown_output)
            print(f"  Merged content written to '{output_file}'")
        except Exception as e:
            print(f"An error occurred while writing to '{output_file}': {e}")


def main():
    """
    Entry point of the script. Parses command-line arguments and initiates folder processing.
    """
    parser = argparse.ArgumentParser(
        description="Recursively merge Markdown files into index.md based on headings."
    )
    parser.add_argument(
        "root_dir", help="Root directory containing Markdown files and subdirectories."
    )
    args = parser.parse_args()

    root_dir = args.root_dir

    if not os.path.isdir(root_dir):
        print(f"Error: The directory '{root_dir}' does not exist.")
        sys.exit(1)

    process_folder(root_dir, is_root=True)


if __name__ == "__main__":
    main()
