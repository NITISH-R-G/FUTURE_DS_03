import os
import ast
import re
import builtins

def get_repo_structure(path='.', exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.github', '__pycache__', 'venv', 'node_modules']

    structure = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        level = root.replace(path, '').count(os.sep)
        indent = ' ' * 4 * level
        folder = os.path.basename(root)
        if folder:
            structure.append(f"{indent}- **{folder}/**")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            structure.append(f"{subindent}- {f}")
    return '\n'.join(structure)

def analyze_dependencies(path='.', exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.github', '__pycache__', 'venv', 'node_modules']

    internal_modules = set()
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f.endswith('.py'):
                internal_modules.add(f.replace('.py', ''))

    stdlib = set(dir(builtins)) # Approximation for stdlib to exclude

    external_deps = set()
    internal_deps = set()
    databases = set()
    frameworks = set()

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if not f.endswith('.py'):
                continue

            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    node = ast.parse(file.read())
                    for n in ast.walk(node):
                        if isinstance(n, ast.Import):
                            for alias in n.names:
                                base_module = alias.name.split('.')[0]
                                if base_module in internal_modules:
                                    internal_deps.add(base_module)
                                else:
                                    external_deps.add(base_module)
                        elif isinstance(n, ast.ImportFrom):
                            if n.module:
                                base_module = n.module.split('.')[0]
                                if base_module in internal_modules or n.level > 0:
                                    internal_deps.add(base_module)
                                else:
                                    external_deps.add(base_module)
            except Exception:
                pass

    for dep in external_deps:
        if dep in ['sqlite3', 'psycopg2', 'sqlalchemy', 'pymongo', 'redis']:
            databases.add(dep)
        if dep in ['flask', 'django', 'fastapi', 'streamlit']:
            frameworks.add(dep)

    deps_md = "### Dependency Knowledge Graph\n\n"
    if external_deps:
        deps_md += "**External Dependencies:**\n" + ", ".join([f"`{d}`" for d in sorted(external_deps)]) + "\n\n"
    if internal_deps:
        deps_md += "**Internal Module Interactions:**\n" + ", ".join([f"`{d}`" for d in sorted(internal_deps)]) + "\n\n"

    if databases:
        deps_md += "**Databases Detected:**\n" + ", ".join([f"`{d}`" for d in sorted(databases)]) + "\n\n"

    return deps_md, list(frameworks), list(databases)

def detect_tech_stack(frameworks, databases):
    stack = []
    if os.path.exists('requirements.txt') or os.path.exists('setup.py') or os.path.exists('Pipfile'):
        stack.append("- **Python**: Primary language.")
    if os.path.exists('package.json'):
        stack.append("- **Node.js**: JavaScript/TypeScript environment.")
    if os.path.exists('Dockerfile'):
        stack.append("- **Docker**: Containerization.")
    if os.path.exists('.github/workflows'):
        stack.append("- **GitHub Actions**: CI/CD automation.")

    for fw in frameworks:
        stack.append(f"- **{fw.capitalize()}**: Web/Application framework.")
    for db in databases:
        stack.append(f"- **{db.capitalize()}**: Database integration.")

    if not stack:
        stack.append("- No specific tech stack files detected yet.")
    return '\n'.join(stack)

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
    print("Running Repository Analyzer...")

    structure_md = get_repo_structure()
    update_readme('REPO_STRUCTURE', structure_md)

    deps_md, frameworks, databases = analyze_dependencies()
    update_readme('DEPENDENCIES', deps_md)

    tech_stack_md = detect_tech_stack(frameworks, databases)
    update_readme('TECH_STACK', tech_stack_md)

    print("Repository analysis complete.")
