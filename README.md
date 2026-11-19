# FileMind

**A smart, safe, terminal-first file manager.**  
Created by **zx0-01**.

FileMind helps you understand, search, clean up, and organize files without risking accidental data loss. It is designed to be preview-first: organizing never moves anything unless you explicitly pass `--apply`.

## Features

- Scan folders and summarize file types, total size, and file count.
- Find duplicate files using SHA-256 (not just matching names).
- Find the largest files.
- Search by filename, extension, and optional case-insensitive matching.
- Organize files into folders by file type with a dry-run preview.
- Export scan reports as JSON.
- Cross-platform: Linux, macOS, and Windows.
- No telemetry. Data stays on your computer.

## Install

Python 3.10 or newer is required.

### Linux / macOS

```bash
git clone https://github.com/yourname/filemind.git
cd filemind
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Windows PowerShell

```powershell
git clone https://github.com/yourname/filemind.git
cd filemind
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -e .
```

## Quick start

```bash
filemind scan ~/Downloads
filemind largest ~/Downloads --limit 15
filemind duplicates ~/Downloads
filemind search ~/Documents "invoice"
filemind organize ~/Downloads
filemind organize ~/Downloads --apply
filemind report ~/Downloads --output report.json
```

On Windows, use paths such as `C:\Users\YourName\Downloads`.

## Commands

| Command | Description |
|---|---|
| `filemind scan PATH` | Folder overview and file-type summary |
| `filemind largest PATH --limit 10` | Largest files |
| `filemind duplicates PATH` | SHA-256 duplicate detection |
| `filemind search PATH QUERY` | Search filenames |
| `filemind organize PATH` | Preview organization plan |
| `filemind organize PATH --apply` | Apply the plan |
| `filemind report PATH --output report.json` | Export JSON report |
| `filemind --help` | Show help |

## Safety

- `organize` is preview-only unless `--apply` is supplied.
- Existing destination names are never overwritten; a numbered filename is chosen.
- Symlinks are skipped during recursive scans.
- File operations are limited to the selected folder tree.
- Always keep a backup of important files. FileMind is a helper, not a backup system.

## File categories

Images, Videos, Audio, Documents, Archives, Code, Installers, and Other. Unknown extensions go into `Other`.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## License

MIT
