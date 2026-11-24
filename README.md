# FileMind

**A smart, safe, terminal-first file manager for Python.**

FileMind helps you understand, search, find duplicates, and organize files from your terminal. Its organizing workflow is preview-first: it shows a plan and does not move files unless you explicitly pass `--apply` and confirm the action.

## Highlights

- **Folder overview:** count files, calculate total size, and group files by type.
- **Largest files:** find the biggest files recursively.
- **Duplicate finder:** identify byte-identical files recursively using file size and SHA-256.
- **Filename search:** search recursively, with an optional extension filter.
- **Safe organization:** preview root-level files grouped into category folders before applying moves.
- **JSON reports:** export a machine-readable folder summary.
- **Local-first:** FileMind has no telemetry and does not upload file contents.

## Requirements

- Python 3.10 or newer.
- Linux, macOS, or Windows.

## Install from a source checkout

Clone the repository after it has been published. Replace `OWNER/REPOSITORY` with the actual GitHub account and repository name:

```bash
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY
python -m venv .venv
```

Activate the environment:

**Linux / macOS (bash or zsh):**

```bash
source .venv/bin/activate
```

**Linux (Fish):**

```fish
source .venv/bin/activate.fish
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

Install FileMind:

```bash
python -m pip install --upgrade pip
python -m pip install .
```

For development and tests, install the optional development dependencies:

```bash
python -m pip install -e ".[dev]"
```

On Arch Linux, create and activate the virtual environment before using `python -m pip`. Do not install project dependencies into the system Python environment.

## Quick start

```bash
filemind --help
filemind scan ~/Downloads
filemind largest ~/Downloads --limit 15
filemind duplicates ~/Downloads
filemind search ~/Documents invoice
filemind search ~/Documents invoice --ext .pdf
filemind organize ~/Downloads
filemind organize ~/Downloads --apply
filemind report ~/Downloads --output report.json
```

You can also run FileMind without the installed console command:

```bash
python -m filemind --help
python -m filemind scan ~/Downloads
```

On Windows, use paths such as `C:\Users\YourName\Downloads`.

## Commands

| Command | What it does | Changes files? |
|---|---|---:|
| `filemind scan PATH` | Summarizes file count, size, and categories | No |
| `filemind largest PATH --limit 10` | Lists the largest files recursively | No |
| `filemind duplicates PATH` | Finds byte-identical files recursively | No |
| `filemind search PATH QUERY` | Searches filenames recursively | No |
| `filemind search PATH QUERY --ext .pdf` | Searches filenames with an extension filter | No |
| `filemind organize PATH` | Previews a file organization plan | No |
| `filemind organize PATH --apply` | Asks for confirmation, then organizes eligible files | Yes, after confirmation |
| `filemind report PATH --output report.json` | Writes a JSON scan report | Writes the report file only |

## How FileMind works

1. **Walk:** it traverses the selected folder and its subfolders without following symbolic links.
2. **Inspect:** it reads file names and metadata such as file size. Duplicate detection reads file contents in chunks to calculate SHA-256 hashes.
3. **Categorize:** file extensions map to categories such as Images, Videos, Audio, Documents, Archives, Code, and Installers. Unknown extensions are classified as Other.
4. **Preview:** the organize command builds and displays a plan before doing anything.
5. **Apply:** when `--apply` is supplied and the user confirms, eligible files directly inside the selected folder are moved into category folders. Existing destination names are preserved; FileMind chooses a numbered alternative.

## Safety behavior and limitations

- Organizing is preview-only unless `--apply` is supplied and confirmed.
- The organizer only considers non-hidden files directly inside the selected folder. It does not flatten or reorganize files already inside subfolders.
- Scan, search, largest-file listing, and duplicate detection traverse subfolders recursively.
- Symbolic links are skipped; their targets are not followed.
- Duplicate detection compares file sizes first, then SHA-256 hashes. It reports duplicates but never deletes them.
- Organizing uses a no-overwrite hard-link operation followed by removal of the source. If the filesystem does not support hard links or the move cannot be completed safely, FileMind reports an error rather than falling back to an overwrite-prone operation. Source and destination therefore need to be on a filesystem that supports hard links.
- FileMind is not a backup tool. Keep backups of important data and review the organize preview before applying it.

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Fish: source .venv/bin/activate.fish
python -m pip install -e ".[dev]"
python -m pytest -v
```

Run the CLI from the source tree:

```bash
python -m filemind --help
```

## Project layout

```text
filemind/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── filemind/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       └── core.py
└── tests/
    └── test_core.py
```

## License

FileMind is released under the MIT License. See [LICENSE](LICENSE).

## About

FileMind is a Python command-line project by **zx0-01**. It is built for people who want a clear overview of their folders and practical file organization tools, while keeping file operations explicit and under the user's control.
