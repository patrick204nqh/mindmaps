# scripts/merge_markmap/merger.py

from collections import defaultdict
from .utils import extract_text
import logging


def extract_lists(nodes, indent_level=0):
    """
    Recursively extracts list items from AST nodes as structured dictionaries.
    
    Args:
        nodes (list): List of AST nodes.
        indent_level (int): Current indentation level.
    
    Returns:
        list: List of dictionaries representing list items.
    """
    list_items = []
    for node in nodes:
        if node['type'] == 'list':
            # ordered = node.get('ordered', False)
            for item in node.get('children', []):
                if item['type'] == 'list_item':
                    # Extract text from 'paragraph' or 'block_text' nodes
                    item_text = ""
                    for child in item.get('children', []):
                        if child['type'] in ['paragraph', 'block_text']:
                            item_text += extract_text(child).strip()
                    # Create a dictionary for the list item
                    list_item = {'text': item_text, 'children': []}
                    # Extract nested lists
                    nested_lists = [child for child in item.get('children', []) if child.get('type') == 'list']
                    for nested in nested_lists:
                        list_item['children'].extend(extract_lists([nested], indent_level + 1))
                    list_items.append(list_item)
    return list_items


def merge_list_items(existing_items, new_items):
    """
    Merges new_items into existing_items based on the 'text' field.
    
    Args:
        existing_items (list): Existing list of items.
        new_items (list): New list of items to merge.
    """
    for new_item in new_items:
        # Check if the item already exists
        match = next((item for item in existing_items if item['text'] == new_item['text']), None)
        if match:
            # If it exists, merge their children recursively
            merge_list_items(match['children'], new_item['children'])
        else:
            # If it doesn't exist, append it
            existing_items.append(new_item)


def merge_asts(asts):
    """
    Merges multiple ASTs based on headings.
    Returns the main heading, merged content, and combined front matter.
    
    Args:
        asts (list): List of ASTs to merge.
    
    Returns:
        tuple: (main_heading, merged_content, combined_front_matter)
    """
    merged_content = defaultdict(list)
    main_heading = None
    combined_front_matter = None

    for ast_index, ast in enumerate(asts):
        current_heading = None  # Reset current heading for each file
        skip_next_heading = False  # Flag to skip front matter headings
        logging.info(f"\nProcessing AST {ast_index + 1}")
        for element in ast:
            element_type = element.get('type', '')

            # Handle front matter: skip heading immediately after 'thematic_break'
            if skip_next_heading:
                if element_type == 'heading':
                    logging.debug("  Skipping heading as front matter.")
                skip_next_heading = False
                continue

            if element_type == 'thematic_break':
                logging.debug("  Found 'thematic_break', will skip next heading as front matter.")
                skip_next_heading = True
                continue

            if element_type in ['front_matter', 'yaml', 'block_quote']:
                logging.debug(f"  Skipping '{element_type}' element.")
                continue

            if element_type == 'heading':
                # Retrieve 'level' from 'attrs'
                heading_level = element.get('attrs', {}).get('level', 1)
                heading_text = extract_text(element).strip()
                logging.info(f"  Found heading: Level {heading_level} - '{heading_text}'")

                # Skip unwanted headings (e.g., markmap-related headings)
                if "markmap" in heading_text.lower():
                    logging.debug("    Skipping 'markmap' heading.")
                    continue

                if heading_level == 1:
                    if not main_heading:
                        main_heading = heading_text
                        logging.info(f"    Set main heading: '{main_heading}'")
                    elif heading_text == main_heading:
                        logging.info(f"    Encountered duplicate main heading: '{heading_text}'. Continuing to accumulate content.")
                    else:
                        logging.info(f"    Ignoring different main heading: '{heading_text}'")
                        continue
                elif heading_level == 2:
                    current_heading = heading_text
                    logging.info(f"    Set current subheading: '{current_heading}'")
            elif element_type == 'list':
                if current_heading:
                    logging.info(f"  Found list under subheading: '{current_heading}'")
                    # Extract list items as structured dictionaries
                    list_items = extract_lists([element], indent_level=1)
                    logging.debug(f"    Extracted list items: {list_items}")
                    # Merge into the existing subheading
                    merge_list_items(merged_content[current_heading], list_items)
                elif main_heading:
                    logging.info(f"  Found list directly under main heading: '{main_heading}'")
                    # Extract list items with no indentation
                    list_items = extract_lists([element], indent_level=0)
                    logging.debug(f"    Extracted list items: {list_items}")
                    # Merge into the main heading
                    merge_list_items(merged_content[main_heading], list_items)
                else:
                    logging.warning("  Found a list without a current subheading or main heading. Skipping.")

    logging.info(f"\nMain Heading: '{main_heading}'")
    logging.info("Merged Content:")
    for heading, items in merged_content.items():
        logging.info(f"  {heading}:")
        for item in items:
            logging.info(f"    {item}")

    return main_heading, merged_content, combined_front_matter