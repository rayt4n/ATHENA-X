"""ATHENA-X Migration Export — Create a single ZIP archive of the entire project.

Includes: source code, reports, PDFs, worklogs, architecture docs, tests,
screenshots, configuration files.

Excludes: .venv, skills/, __pycache__, .pytest_cache, *.pyc, node_modules,
.git, .next (build artifacts and tooling not part of the project).
"""
from __future__ import annotations
import hashlib
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/z/my-project")
OUT_ZIP = Path("/home/z/my-project/download/athena-x-migration-export.zip")

# Directories to exclude (not project content)
EXCLUDE_DIRS = {
    ".venv", "skills", "__pycache__", ".pytest_cache", "node_modules",
    ".git", ".next", ".turbo", ".zscripts", ".egg-info",
    "build", "dist", ".mypy_cache", ".ruff_cache",
}

# File patterns to exclude
EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".so", ".dylib", ".egg"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db", "dev.pid"}


def should_exclude(path: Path) -> bool:
    """Check if a file/directory should be excluded from the ZIP."""
    parts = path.parts
    # Check if any parent directory is in EXCLUDE_DIRS
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
        # Exclude .egg-info directories
        if part.endswith(".egg-info"):
            return True
    # Check file extension
    if path.is_file() and path.suffix in EXCLUDE_EXTENSIONS:
        return True
    # Check specific files
    if path.name in EXCLUDE_FILES:
        return True
    return False


def add_dir_to_zip(zipf: zipfile.ZipFile, dir_path: Path, base: Path, root_name: str):
    """Recursively add a directory to the ZIP, applying exclusions."""
    for item in sorted(dir_path.iterdir()):
        if should_exclude(item):
            continue
        arcname = Path(root_name) / item.relative_to(base)
        if item.is_dir():
            # Add empty directory entry
            zipf.writestr(str(arcname) + "/", "")
            add_dir_to_zip(zipf, item, base, root_name)
        elif item.is_file():
            zipf.write(str(item), str(arcname))


def add_file_to_zip(zipf: zipfile.ZipFile, file_path: Path, base: Path, root_name: str):
    """Add a single file to the ZIP."""
    if should_exclude(file_path):
        return
    arcname = Path(root_name) / file_path.relative_to(base)
    zipf.write(str(file_path), str(arcname))


def create_zip():
    """Create the migration ZIP archive."""
    print(f"[Migration] Creating ZIP archive: {OUT_ZIP}")
    print(f"[Migration] Source: {ROOT}")
    print()

    # Items to include from /home/z/my-project/
    include_dirs = ["athena-x", "scripts", "download", "analysis"]
    include_files = [
        "worklog.md", ".env", ".gitignore", "Caddyfile",
        "components.json", "package.json", "tsconfig.json",
    ]
    # Add vlm-result JSONs
    for f in ROOT.glob("vlm-result-*.json"):
        include_files.append(f.name)

    # Counters
    file_count = 0
    dir_count = 0
    total_size = 0

    with zipfile.ZipFile(OUT_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        # Add directories
        for dirname in include_dirs:
            dir_path = ROOT / dirname
            if not dir_path.exists():
                print(f"  SKIP (not found): {dirname}/")
                continue
            print(f"  Adding: {dirname}/ ...", end=" ", flush=True)
            count_before = file_count
            add_dir_to_zip(zipf, dir_path, ROOT, "athena-x-migration")
            # Count files added
            for _ in dir_path.rglob("*"):
                if _.is_file() and not should_exclude(_):
                    file_count += 1
                    total_size += _.stat().st_size
            print(f"{file_count - count_before} files")

        # Add individual files
        print(f"  Adding: root config files ...", end=" ", flush=True)
        root_count = 0
        for filename in include_files:
            file_path = ROOT / filename
            if file_path.exists():
                add_file_to_zip(zipf, file_path, ROOT, "athena-x-migration")
                file_count += 1
                total_size += file_path.stat().st_size
                root_count += 1
        print(f"{root_count} files")

    zip_size = OUT_ZIP.stat().st_size
    print()
    print(f"[Migration] ZIP archive created successfully.")
    print(f"  Files included: {file_count}")
    print(f"  Uncompressed size: {total_size / 1024 / 1024:.1f} MB")
    print(f"  Compressed size: {zip_size / 1024 / 1024:.1f} MB")
    print(f"  Compression ratio: {(1 - zip_size / total_size) * 100:.1f}%")
    return file_count, total_size, zip_size


def verify_zip() -> bool:
    """Verify the ZIP archive is not corrupted."""
    print(f"\n[Migration] Verifying ZIP integrity...")
    try:
        with zipfile.ZipFile(OUT_ZIP, 'r') as zipf:
            bad_file = zipf.testzip()
            if bad_file is None:
                print(f"  ✓ ZIP archive is valid — no corruption detected.")
                # Count entries
                entries = zipf.namelist()
                print(f"  ✓ Total entries in archive: {len(entries)}")
                return True
            else:
                print(f"  ✗ CORRUPTION detected in: {bad_file}")
                return False
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False


def list_top_level():
    """List top-level folders in the ZIP."""
    print(f"\n[Migration] Top-level contents:")
    with zipfile.ZipFile(OUT_ZIP, 'r') as zipf:
        # Get unique top-level entries
        top_level = set()
        for name in zipf.namelist():
            parts = name.split("/")
            if len(parts) > 0 and parts[0]:
                top_level.add(parts[0])
        for item in sorted(top_level):
            # Check if it's a directory or file
            is_dir = any(name.startswith(item + "/") for name in zipf.namelist() if name != item + "/")
            if is_dir:
                # Count files inside
                count = sum(1 for n in zipf.namelist() if n.startswith(item + "/") and not n.endswith("/"))
                print(f"  📁 {item}/ ({count} files)")
            else:
                info = zipf.getinfo(item)
                print(f"  📄 {item} ({info.file_size:,} bytes)")


def generate_checksum():
    """Generate SHA-256 checksum of the ZIP file."""
    print(f"\n[Migration] Generating SHA-256 checksum...")
    sha256_hash = hashlib.sha256()
    with open(OUT_ZIP, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    checksum = sha256_hash.hexdigest()
    print(f"  SHA-256: {checksum}")

    # Save checksum to file
    checksum_file = OUT_ZIP.with_suffix(".zip.sha256")
    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  {OUT_ZIP.name}\n")
    print(f"  Checksum saved to: {checksum_file}")
    return checksum


def main():
    print("=" * 70)
    print("ATHENA-X Migration Export")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    # Step 1: Create ZIP
    file_count, total_size, zip_size = create_zip()

    # Step 2: Verify integrity
    if not verify_zip():
        print("\n[Migration] FAILED — ZIP archive is corrupted.")
        sys.exit(1)

    # Step 3: List top-level contents
    list_top_level()

    # Step 4: Generate SHA-256 checksum
    checksum = generate_checksum()

    # Summary
    print()
    print("=" * 70)
    print("MIGRATION EXPORT COMPLETE")
    print("=" * 70)
    print(f"  Archive:       {OUT_ZIP}")
    print(f"  Size:          {zip_size:,} bytes ({zip_size / 1024 / 1024:.1f} MB)")
    print(f"  Files:         {file_count}")
    print(f"  Uncompressed:  {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
    print(f"  SHA-256:       {checksum}")
    print(f"  Checksum file: {OUT_ZIP.with_suffix('.zip.sha256')}")
    print()
    print("The ZIP archive is ready for download.")
    print("=" * 70)


if __name__ == "__main__":
    main()
