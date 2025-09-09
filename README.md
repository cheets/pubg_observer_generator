# PUBG Observer Generator

A tool for generating PUBG team observer packages and automatically adding slot numbers to team logos.

## 📂 Project Structure

This directory (`pubg_observer_generator/`) contains the complete project:

- `main.py` - Main application code
- `pyproject.toml` - Poetry configuration
- `poetry.lock` - Dependency lock file
- `.tool-versions` - Python version specification (asdf)

## Features

- 🔍 **Smart Color Analysis**: Analyzes team logos to extract dominant colors
- 🎨 **Automatic Slot Numbers**: Adds slot numbers to team logos with white text and black outline
- 📊 **CSV Generation**: Creates TeamInfo.csv with team data and colors
- 🗂️ **Organized Workflow**: Uses separate directories for clean logos and processed images

## Installation

### Prerequisites

- [asdf](https://asdf-vm.com/) for Python version management
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- Python 3.13+

### Setup

1. **Install asdf plugins:**
   ```bash
   asdf plugin-add python
   asdf plugin-add poetry
   ```

2. **Install Python and Poetry versions with asdf:**
   ```bash
   asdf install
   ```

3. **Install dependencies with Poetry:**
   ```bash
   poetry install
   ```

   This will create a virtual environment using asdf's Python version and install all dependencies.

## Usage

### Input Directory Structure

Organize your images under the `content/` directory:

```
content/
└── league_name/
    └── season/
        └── division/
            ├── logos/           # Clean original team logos
            └── Slots.txt        # Team slot information
```

**Example:** `content/kanaliiga/s15/div4/`

### Slots.txt Format

```
3. Team Name One
4. Team Name Two
5. Another Team
...
```

### Output Structure

The tool generates files in a `content/generated/` directory:

```
content/
├── generated/
│   └── league_name-season-division/
│       ├── Observer/
│       │   ├── TeamIcon/        # Numbered team logos
│       │   └── TeamInfo.csv     # Generated team information
│       └── league_name-season-division.zip    # Zip archive containing only TeamIcon/ and TeamInfo.csv
└── league_name/
    └── season/
        └── division/             # Your input data goes here
```

### Running the Tool

```bash
# Run with Poetry (recommended)
poetry run generator <league_name> <season> <division>

# Example with example data
poetry run generator example s15 div4

# Example with your own data
poetry run generator your_league season_1 division_a

# Or use the shorter command
poetry run app kanaliiga s15 div4
```

The tool will:
1. Read images from `content/league_name/season/division/logos/`
2. Read team slots from `content/league_name/season/division/Slots.txt`
3. Generate numbered logos in `content/generated/league_name-season-division/Observer/TeamIcon/`
4. Create team information in `content/generated/league_name-season-division/Observer/TeamInfo.csv`
5. Create a zip archive containing only `TeamIcon/` folder and `TeamInfo.csv` file

## Workflow

1. **Input**: `logos/` directory with clean team logos (or `TeamIcon/` if `logos/` doesn't exist)
2. **Analysis**: Extracts dominant colors from logos using smart color detection
3. **Processing**: Adds slot numbers to logos and saves to `TeamIcon/`
4. **Output**: Generates `TeamInfo.csv` with team information and colors

## Color Analysis Features

- 🎯 **Smart Color Selection**: Prioritizes vibrant colors over grays/blacks
- 🔄 **Saturation Analysis**: Uses color saturation to select the best colors
- ⚖️ **Fallback Logic**: Handles edge cases like all-gray logos
- 🎨 **Unique Colors**: Ensures no two teams get identical colors

## Requirements

- Python 3.13+
- Pillow (PIL) for image processing

## Development

### Running Development Tasks

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Fix linting issues automatically
poetry run ruff check . --fix
```

## License

MIT License

## 📁 Complete Project Structure

```
pubg_observer_generator/
├── pyproject.toml          # Poetry configuration & dependencies (contains script definitions)
├── poetry.lock            # Locked dependency versions
├── .tool-versions         # Python (3.13.7) and Poetry (2.1.3) versions for asdf
├── .gitignore            # Git ignore patterns (ignores generated/*, tracks example/)
├── README.md             # This documentation
├── content/              # Project content and generated files
│   ├── generated/        # Generated output (gitignored)
│   └── example/          # Example input data (version controlled)
├── src/                  # Source code directory
│   └── pubg_observer_generator/
│       ├── __init__.py   # Package initialization
│       └── main.py       # Main application code
├── tests/                # Test files
│   └── test_short_names.py        # Unit tests for short name generation
```

## 🧪 Testing

Run the tests to verify functionality:

```bash
# Run tests
poetry run pytest

# Test the full generator with example data
poetry run generator example s15 div4
```

Note: Example data is available in `content/example/` directory.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
