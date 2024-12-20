import yaml
import os


def load_settings(config_path=None):
    """
    Loads the configuration from a YAML file.
    """
    # If no path is provided, set the path relative to this script's directory
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "settings.yml")

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def get_markmap_config():
    """
    Returns the Markmap front matter as a string for markdown files, correctly wrapped under the 'markmap' key.
    """
    config = load_settings()
    if config and "markmap" in config:
        # Wrap the markmap configuration under the 'markmap' key
        markmap_config = {"markmap": config["markmap"]}
        front_matter = (
            f"---\n{yaml.dump(markmap_config, default_flow_style=False)}---\n\n"
        )
        return front_matter
    return ""


def get_formatting_settings():
    """
    Returns the formatting settings like indentation size and line spacing.
    """
    config = load_settings()
    if config:
        return config["formatting"]
    return {"indent_size": 2, "line_spacing": 1}  # Default fallback values


def get_output_file_name():
    config = load_settings()
    if config and "output" in config:
        return config["output"].get(
            "output_file_name", ".wrapped.mm.md"
        )  # Default to '.wrapped.mm.md'
    return ".wrapped.mm.md"
