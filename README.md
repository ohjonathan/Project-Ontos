# Ontos: The Context Operating System

Ontos is a local-first CLI tool that helps you manage your project documentation as a semantic knowledge graph. It solves "Context Fragmentation" by transforming static Markdown files into a structured, queryable ontology.

## Installation

### Prerequisites
- Python 3.9+

### Global Installation (Recommended for Usage)
To use `ontos` from any directory without activating a virtual environment:

1. Build the package:
   ```bash
   cd /path/to/Ontos  # Navigate to the project directory first!
   /usr/bin/python3 -m build
   ```
2. Install the built wheel globally:
   ```bash
   /usr/bin/python3 -m pip install --user dist/ontos-0.1.0-py3-none-any.whl
   ```
3. **Important:** Ensure your user binary directory is in your PATH.
   Add this to your `~/.zshrc` or `~/.bashrc`:
   ```bash
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"
   ```
   *(Note: The python version (3.9) may vary. Check the install output.)*

### Local Installation (Development)
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

### 1. Sanitize Documentation
Check for "monolith" files and missing headers.
```bash
ontos groom /path/to/docs
```

### 2. Initialize Ontology
Scan directory, tag files, and inject YAML frontmatter.
```bash
ontos init /path/to/docs
```

### 3. Visualize Graph
See the hierarchy of your documentation.
```bash
ontos map /path/to/docs
```

### 4. Retrieve Smart Context
Get laser-focused context for a task (copied to clipboard).
```bash
ontos context "payment integration" --directory /path/to/docs
```

### 5. Check for Drift
Find documents that are out of sync with their parents.
```bash
ontos doctor /path/to/docs
```
