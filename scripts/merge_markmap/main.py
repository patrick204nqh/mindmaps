import os
import sys
import argparse
import logging
from .parser import parse_markdown_to_ast
from .merger import merge_asts
from .converter import convert_ast_to_markdown
from .utils import extract_front_matter
from .config import get_markmap_config, get_formatting_settings, get_output_file_name

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def merge_child_index(folder_path, subdir_name, seen_headings):
    """
    Merges the content of a child .wrapped.mm.md into the parent .wrapped.mm.md.
    Removes front matter and duplicate headings if present in the child content.

    Args:
        folder_path (str): Path to the parent folder.
        subdir_name (str): Name of the subdirectory.
        seen_headings (set): A set to track already seen headings.

    Returns:
        list: Lines of merged content without duplicate headings and without front matter.
    """
    subdir_index_path = os.path.join(
        folder_path, subdir_name, get_output_file_name()
    )  # Use custom output file name
    if not os.path.isfile(subdir_index_path):
        print(f"  Warning: '{subdir_index_path}' does not exist. Skipping.")
        return []

    try:
        with open(subdir_index_path, "r", encoding="utf-8") as f:
            sub_content = f.read()

        # Remove front matter if present
        front_matter, content_without_fm = extract_front_matter(sub_content)

        # Split into lines
        lines = content_without_fm.splitlines()

        # Remove duplicate headings like '# Grammar'
        clean_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("# "):
                if stripped_line not in seen_headings:
                    seen_headings.add(stripped_line)
                    clean_lines.append(line)
                else:
                    # Skip duplicate headings
                    print(
                        f"  Skipping duplicate heading '{stripped_line}' from '{subdir_index_path}'."
                    )
            else:
                clean_lines.append(line)

        return clean_lines
    except Exception as e:
        print(f"  Error reading '{subdir_index_path}': {e}")
        return []


def process_folder(folder_path, is_root=False, front_matter_path=None):
    """
    Processes a folder:
    1. Recursively processes all subdirectories.
    2. Merges all Markdown files in the current folder into the configured output file (default: .wrapped.mm.md).
    3. Appends content from subdirectories' output files in the current folder's output file.

    Args:
        folder_path (str): Path to the current folder.
        is_root (bool): Flag indicating if the current folder is the root folder.
        front_matter_path (str): Path to a custom front matter file (optional).
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

    # Initialize a shared set to track seen headings
    seen_headings = set()

    # Step 2: Recursively process each subdirectory first (depth-first)
    for subdir in subdirs:
        process_folder(os.path.join(folder_path, subdir), is_root=False)

    if is_root:
        # Step 3: Prepare the final output content for the root file
        markdown_output = (
            get_markmap_config() + "\n"
        )  # Only use front matter from config

        # Step 4: Append content from subdirectories' output files
        for subdir in subdirs:
            subdir_content = merge_child_index(folder_path, subdir, seen_headings)
            if subdir_content:
                markdown_output = (
                    markdown_output.rstrip()
                    + "\n\n"
                    + "\n".join(subdir_content).strip()
                    + "\n"
                )
                print(
                    f"  Merged content from '{subdir}/{get_output_file_name()}' into '{folder_path}/{get_output_file_name()}'"
                )

        # Step 5: Write the final output file at the root level
        output_file = os.path.join(folder_path, get_output_file_name())
        try:
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(markdown_output.strip() + "\n")
            print(f"  Merged content written to '{output_file}'")
        except Exception as e:
            print(f"An error occurred while writing to '{output_file}': {e}")

    else:
        # Non-root folder: Merge own .mm.md files into the output file
        markdown_files = sorted(
            [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.endswith(".mm.md") and f.lower() != get_output_file_name()
            ]
        )

        asts = []
        front_matters = []
        for file in markdown_files:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                fm, content_no_fm = extract_front_matter(content)
                if fm:
                    front_matters.append(fm)
                ast = parse_markdown_to_ast(file)
                if ast:
                    asts.append(ast)

        if asts:
            main_heading, merged_content, _ = merge_asts(asts)
            # Use the first front matter found, else load from config
            selected_front_matter = get_markmap_config().strip("---\n")
            merged_ast = merged_content[main_heading]
            markdown_output = convert_ast_to_markdown(
                main_heading,
                merged_ast,
                front_matter=selected_front_matter,
                include_front_matter=True,
            )
        else:
            markdown_output = get_markmap_config() + "\n"

        # Step 3: Append content from subdirectories' output files
        for subdir in subdirs:
            subdir_content = merge_child_index(folder_path, subdir, seen_headings)
            if subdir_content:
                markdown_output = (
                    markdown_output.rstrip()
                    + "\n\n"
                    + "\n".join(subdir_content).strip()
                    + "\n"
                )
                print(
                    f"  Merged content from '{subdir}/{get_output_file_name()}' into '{folder_path}/{get_output_file_name()}'"
                )

        # Step 4: Write to output file with the default front matter
        output_file = os.path.join(folder_path, get_output_file_name())
        try:
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(markdown_output.strip() + "\n")
            print(f"  Merged content written to '{output_file}'")
        except Exception as e:
            print(f"An error occurred while writing to '{output_file}': {e}")


def main():
    """
    Entry point of the script. Parses command-line arguments and initiates folder processing.
    """
    parser = argparse.ArgumentParser(
        description="Recursively merge .mm.md files into the configured output file based on headings."
    )
    parser.add_argument(
        "root_dir", help="Root directory containing .mm.md files and subdirectories."
    )
    parser.add_argument(
        "--front-matter", help="Path to a custom front matter file.", default=None
    )
    args = parser.parse_args()

    root_dir = args.root_dir
    front_matter_path = args.front_matter

    if not os.path.isdir(root_dir):
        logging.error(f"The directory '{root_dir}' does not exist.")
        sys.exit(1)

    process_folder(root_dir, is_root=True, front_matter_path=front_matter_path)


if __name__ == "__main__":
    main()
