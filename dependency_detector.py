import ast
import os
import sys
import subprocess
import logging

# Mapping of common import names to their pip package names
IMPORT_TO_PACKAGE = {
    "telebot": "pyTelegramBotAPI",
    "aiogram": "aiogram",
    "requests": "requests",
    "flask": "flask",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "django": "django",
    "sqlalchemy": "sqlalchemy",
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "PIL": "Pillow",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "pytz": "pytz",
    "dateutil": "python-dateutil",
    "yaml": "PyYAML",
    "redis": "redis",
    "pymongo": "pymongo",
    "mysql": "mysql-connector-python",
    "psycopg2": "psycopg2-binary",
    "telegram": "python-telegram-bot",
    "pyTelegramBotAPI": "pyTelegramBotAPI",
    "aiohttp": "aiohttp",
    "motor": "motor",
    "tortoise": "tortoise-orm",
    "beanie": "beanie",
    "pydantic": "pydantic",
    "lxml": "lxml",
    "cryptography": "cryptography",
}

def get_imports_from_file(file_path):
    """Extract all top-level imports from a Python file."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Remove BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
            
        tree = ast.parse(content.decode('utf-8', errors='ignore'))
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports
    except Exception as e:
        logging.error(f"Error parsing {file_path}: {e}")
        return set()

def detect_dependencies(bot_dir):
    """Detect all required packages for a bot directory."""
    all_imports = set()
    for root, _, files in os.walk(bot_dir):
        for file in files:
            if file.endswith('.py'):
                all_imports.update(get_imports_from_file(os.path.join(root, file)))
    
    # Filter out standard library modules
    # We can use a simple list of common stdlib modules
    # For simplicity, let's use a list of common ones and check if they are in sys.modules
    # or if they are part of the standard library.
    
    # A better way: check if the module is part of the standard library
    import sysconfig
    stdlib_path = sysconfig.get_path('stdlib')
    
    dependencies = []
    for imp in all_imports:
        if imp in IMPORT_TO_PACKAGE:
            dependencies.append(IMPORT_TO_PACKAGE[imp])
        else:
            # Check if it's a local file
            if os.path.exists(os.path.join(bot_dir, f"{imp}.py")) or \
               os.path.isdir(os.path.join(bot_dir, imp)):
                continue
            
            # Check if it's in stdlib
            if imp in sys.builtin_module_names:
                continue
            
            # Check if it's in the stdlib directory
            if os.path.exists(os.path.join(stdlib_path, f"{imp}.py")) or \
               os.path.isdir(os.path.join(stdlib_path, imp)):
                continue
            
            # Common stdlib modules that might not be caught
            if imp in ['asyncio', 'json', 'logging', 'os', 'shutil', 'signal', 'sqlite3', 'subprocess', 'sys', 'time', 'ast', 'typing', 'datetime', 'random', 're', 'math']:
                continue
                
            dependencies.append(imp)
                
    return sorted(list(set(dependencies)))

def install_dependencies(dependencies, log_file=None):
    """Install a list of dependencies using pip."""
    if not dependencies:
        return True
    
    cmd = [sys.executable, "-m", "pip", "install"] + dependencies
    try:
        if log_file:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"Installing: {', '.join(dependencies)}\n")
                subprocess.run(cmd, stdout=f, stderr=f, check=True)
        else:
            subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        if log_file:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"Installation failed: {e}\n")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dependency_detector.py <bot_directory>")
        sys.exit(1)
    
    bot_path = sys.argv[1]
    deps = detect_dependencies(bot_path)
    print(f"Detected dependencies: {deps}")
    
    req_file = os.path.join(bot_path, "requirements.txt")
    with open(req_file, "w", encoding="utf-8") as f:
        for dep in deps:
            f.write(f"{dep}\n")
    print(f"Created {req_file}")
