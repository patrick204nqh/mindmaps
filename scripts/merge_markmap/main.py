# scripts/merge_markmap/main.py

import os
import sys
import argparse
from .parser import parse_markdown_to_ast
from .merger import merge_asts
from .converter import convert_ast_to_markdown
from .utils import extract_front_matter

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


def merge_child_index(folder_path, subdir_name):
    """
    Merges the content of a child index.md into the parent index.md.

    Args:
        folder_path (str): Path to the parent folder.
        subdir_name (str): Name of the subdirectory.
    
    Returns:
        list: Lines of merged content.
    """
    subdir_index_path = os.path.join(folder_path, subdir_name, 'index.md')
    if not os.path.isfile(subdir_index_path):
        print(f"  Warning: '{subdir_index_path}' does not exist. Skipping.")
        return []
    
    try:
        with open(subdir_index_path, 'r', encoding='utf-8') as f:
            sub_content = f.read()
        
        # Remove front matter if present
        front_matter, content_without_front_matter = extract_front_matter(sub_content)
        
        # Return the content without front matter as a list of lines
        return content_without_front_matter.splitlines()
    except Exception as e:
        print(f"  Error reading '{subdir_index_path}': {e}")
        return []


def process_folder(folder_path, is_root=False, front_matter_path=None):
    """
    Processes a folder:
    1. Recursively processes all subdirectories.
    2. Merges all Markdown files in the current folder into index.md.
    3. Appends content from subdirectories' index.md in the current folder's index.md.
    
    Args:
        folder_path (str): Path to the current folder.
        is_root (bool): Flag indicating if the current folder is the root folder.
        front_matter_path (str): Path to a custom front matter file (optional).
    """
    print(f"\nProcessing folder: {folder_path}")

    # Step 1: Collect all subdirectories (sorted for consistent order)
    subdirs = sorted([
        d for d in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, d))
    ])

    # Step 2: Recursively process each subdirectory first (depth-first)
    for subdir in subdirs:
        process_folder(os.path.join(folder_path, subdir), is_root=False)

    if is_root:
        # Initialize markdown_output with root front matter.
        if front_matter_path and os.path.isfile(front_matter_path):
            with open(front_matter_path, 'r', encoding='utf-8') as fm_file:
                custom_front_matter = fm_file.read()
            markdown_output = custom_front_matter + "\n\n"
        else:
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
                print(f"  Merged content from '{subdir}/index.md' into '{folder_path}/index.md'")
        
        # Step 4: Write to root index.md
        output_file = os.path.join(folder_path, 'index.md')
        try:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.write(markdown_output)
            print(f"  Merged content written to '{output_file}'")
        except Exception as e:
            print(f"An error occurred while writing to '{output_file}': {e}")
    else:
        # Non-root folder: Merge own .md files into index.md
        markdown_files = sorted([
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.endswith('.md') and f.lower() != 'index.md'
        ])

        asts = []
        front_matters = []
        for file in markdown_files:
            # Extract front matter and content
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                fm, content_no_fm = extract_front_matter(content)
                if fm:
                    front_matters.append(fm)
                # Parse the content without front matter
                ast = parse_markdown_to_ast(file)
                if ast:
                    asts.append(ast)

        if asts:
            main_heading, merged_content, _ = merge_asts(asts)
            # Use the first front matter found, else default
            selected_front_matter = front_matters[0] if front_matters else DEFAULT_MARKMAP_FRONT_MATTER.strip('---\n')
            # Extract the list associated with the main_heading
            merged_ast = merged_content[main_heading]
            markdown_output = convert_ast_to_markdown(
                main_heading,
                merged_ast,
                front_matter=selected_front_matter,
                include_front_matter=True  # Include front matter for subdirectories
            )
        else:
            # If no own Markdown files, set main_heading to folder name and initialize markdown_output with front matter
            main_heading = os.path.basename(folder_path).capitalize()
            markdown_output = DEFAULT_MARKMAP_FRONT_MATTER + "\n\n" + f"# {main_heading}\n\n"

        # Step 3: Append content from subdirectories' index.md
        for subdir in subdirs:
            subdir_content = merge_child_index(folder_path, subdir)
            if subdir_content:
                # Append a newline for separation
                markdown_output += "\n"
                # Append the child index.md content directly
                markdown_output += "\n".join(subdir_content)
                markdown_output += "\n"
                print(f"  Merged content from '{subdir}/index.md' into '{folder_path}/index.md'")

        # Step 4: Write to index.md
        output_file = os.path.join(folder_path, 'index.md')
        try:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.write(markdown_output)
            print(f"  Merged content written to '{output_file}'")
        except Exception as e:
            print(f"An error occurred while writing to '{output_file}': {e}")


def main():
    """
    Entry point of the script. Parses command-line arguments and initiates folder processing.
    """
    parser = argparse.ArgumentParser(description="Recursively merge Markdown files into index.md based on headings.")
    parser.add_argument('root_dir', help='Root directory containing Markdown files and subdirectories.')
    parser.add_argument('--front-matter', help='Path to a custom front matter file.', default=None)
    args = parser.parse_args()

    root_dir = args.root_dir
    front_matter_path = args.front_matter

    if not os.path.isdir(root_dir):
        print(f"Error: The directory '{root_dir}' does not exist.")
        sys.exit(1)

    process_folder(root_dir, is_root=True, front_matter_path=front_matter_path)


if __name__ == "__main__":
    main()