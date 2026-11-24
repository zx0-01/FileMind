# GitHub repository setup

Use this checklist when publishing FileMind for the first time.

## Repository About text

**Description:** A safe, terminal-first Python file manager to scan, search, find duplicates, and organize files.

**Suggested topics:** `python`, `cli`, `terminal`, `file-manager`, `file-organization`, `duplicate-finder`, `filesystem`, `typer`, `rich`

Do not add a website URL unless you have a real project page.

## Create the repository

1. Sign in to GitHub and create a new repository named `FileMind` (or your preferred name).
2. Keep it public if you want anyone to view it, or private if you are not ready to publish it.
3. Do not ask GitHub to create a README, `.gitignore`, or license if those files already exist in this project.
4. Copy the repository URL shown by GitHub. The commands below use a placeholder; replace it with your real URL.

## Check before publishing

From the project directory:

```bash
git status --short
git diff --check
python -m pytest -v
```

Review every changed file. Confirm that `.venv/`, personal files, secrets, generated reports, caches, and `investigation.cany/` are not staged.

## First publication (only if this folder is not already a Git repository)

```bash
git init
git branch -M main
git add .
git status --short
git commit -m "Release FileMind 2.0.0"
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

Replace the remote URL with the exact URL from your new GitHub repository.

## If the project already has a Git repository

Do **not** run `git init` or add a second remote. Check the existing remote and branch first:

```bash
git remote -v
git branch --show-current
git status --short
```

Then stage and review only the intended project files before committing:

```bash
git add README.md LICENSE pyproject.toml src tests .gitignore CONTRIBUTING.md SECURITY.md CHANGELOG.md GITHUB.md
git diff --cached --check
git diff --cached --stat
git status --short
```

Only after reviewing the staged diff should you create a commit and push to the existing remote. If the existing remote is not the repository you intend to publish to, stop and resolve that first.

## Suggested release notes for v2.0.0

- Added recursive SHA-256 duplicate detection.
- Added progress feedback to long-running scan operations.
- Improved safe file organization to avoid overwriting existing destination files.
- Added `python -m filemind` support.
- Expanded documentation and development setup.
