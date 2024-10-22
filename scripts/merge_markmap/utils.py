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
