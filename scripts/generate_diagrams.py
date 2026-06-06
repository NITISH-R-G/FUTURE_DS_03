import os
import re

def generate_tree_diagram(path='.', exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.github', '__pycache__', 'venv', 'node_modules']

    mermaid_lines = ["```mermaid", "graph TD"]
    click_lines = []

    node_counter = 0
    dir_nodes = {}

    # Root node
    root_node = f"node{node_counter}"
    dir_nodes[os.path.abspath(path)] = root_node
    mermaid_lines.append(f'    {root_node}["root"]:::folder')
    node_counter += 1

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        current_node = dir_nodes.get(os.path.abspath(root))
        if not current_node:
            continue

        for d in dirs:
            dir_path = os.path.abspath(os.path.join(root, d))
            child_node = f"node{node_counter}"
            dir_nodes[dir_path] = child_node
            mermaid_lines.append(f'    {child_node}["{d}/"]:::folder')
            mermaid_lines.append(f'    {current_node} --> {child_node}')

            # Interactive deep linking to directories (GitHub blob/tree url structure)
            rel_path = os.path.relpath(dir_path, path)
            click_lines.append(f'    click {child_node} "{rel_path}" "View {d}"')
            node_counter += 1

        for f in files:
            if f.endswith('.py') or f.endswith('.md') or f.endswith('.yml') or f.endswith('.csv'):
                child_node = f"node{node_counter}"
                mermaid_lines.append(f'    {child_node}["{f}"]')
                mermaid_lines.append(f'    {current_node} --> {child_node}')

                # Interactive deep linking to files
                file_path = os.path.abspath(os.path.join(root, f))
                rel_path = os.path.relpath(file_path, path)
                click_lines.append(f'    click {child_node} "{rel_path}" "View {f}"')
                node_counter += 1

    mermaid_lines.append("    classDef folder fill:#e1f5fe,stroke:#01579b,stroke-width:2px;")
    mermaid_lines.extend(click_lines)
    mermaid_lines.append("```")
    return '\n'.join(mermaid_lines)

def update_readme(section_marker, new_content, readme_path='README.md'):
    try:
        with open(readme_path, 'r') as f:
            content = f.read()

        start_marker = f"<!-- {section_marker}_START -->"
        end_marker = f"<!-- {section_marker}_END -->"

        pattern = re.compile(f"({start_marker}).*?({end_marker})", re.DOTALL)

        if pattern.search(content):
            new_readme_content = pattern.sub(rf"\1\n{new_content}\n\2", content)
            with open(readme_path, 'w') as f:
                f.write(new_readme_content)
            print(f"Updated {section_marker} in README.md")
        else:
            print(f"Markers for {section_marker} not found in README.md")

    except FileNotFoundError:
        print(f"{readme_path} not found.")

if __name__ == "__main__":
    print("Running Diagram Generator...")

    diagram_md = generate_tree_diagram()
    update_readme('DIAGRAMS', diagram_md)

    print("Diagram generation complete.")
