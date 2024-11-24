import os
import hashlib
import json
import logging
from pathlib import Path
import shutil
import typer
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.logging import RichHandler

app = typer.Typer(help="Copy files to target directory, removing duplicates.")

def load_cache(cache_file: Path):
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache_file: Path, cache_data):
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)

def compute_file_hash(file_path: Path):
    hash_obj = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.warning(f"Could not read {file_path}: {e}")
        return None

def get_file_hash(file_path: Path, cache):
    try:
        stat = file_path.stat()
        cache_key = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        if cache_key in cache:
            return cache[cache_key]
        else:
            filehash = compute_file_hash(file_path)
            if filehash:
                cache[cache_key] = filehash
            return filehash
    except Exception as e:
        logging.warning(f"Could not access {file_path}: {e}")
        return None

def files_are_identical(file1: Path, file2: Path):
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            while True:
                b1 = f1.read(8192)
                b2 = f2.read(8192)
                if b1 != b2:
                    return False
                if not b1:
                    return True
    except Exception as e:
        logging.warning(f"Could not compare {file1} and {file2}: {e}")
        return False

def find_duplicates(source_dir: Path, progress, cache):
    files_by_size = {}
    file_sizes = {}
    for file_path in source_dir.rglob('*'):
        if file_path.is_file():
            try:
                size = file_path.stat().st_size
                file_sizes[str(file_path)] = size
                files_by_size.setdefault(size, []).append(file_path)
            except Exception as e:
                logging.warning(f"Could not access {file_path}: {e}")

    potential_dups = [files for files in files_by_size.values() if len(files) > 1]
    files_to_check = [file for group in potential_dups for file in group]

    hash_to_files = {}
    task = progress.add_task("[green]Processing files...", total=len(files_to_check))
    for file_path in files_to_check:
        filehash = get_file_hash(file_path, cache)
        if filehash:
            hash_to_files.setdefault(filehash, []).append(file_path)
        progress.advance(task)

    duplicates = []
    unique_files = []
    for file_list in hash_to_files.values():
        if len(file_list) > 1:
            # Check for hash collisions by comparing files byte by byte
            group = []
            originals = []
            while file_list:
                reference = file_list.pop()
                originals.append(reference)
                group.append({'path': str(reference), 'size': file_sizes[str(reference)]})
                duplicates_in_group = []
                for other_file in file_list[:]:
                    if files_are_identical(reference, other_file):
                        group.append({'path': str(other_file), 'size': file_sizes[str(other_file)]})
                        file_list.remove(other_file)
                if len(group) > 1:
                    duplicates.append(group)
                else:
                    unique_files.append(group[0])
                group = []
        else:
            unique_files.append({'path': str(file_list[0]), 'size': file_sizes[str(file_list[0])]})

    return duplicates, unique_files

@app.command()
def main(
    source_dir: Path = typer.Argument(..., help="Directory to scan for duplicates."),
    target_dir: Path = typer.Argument(..., help="Directory to copy unique files to."),
    output_json: Path = typer.Option("duplicates.json", help="Output JSON file."),
    dryrun: bool = typer.Option(
        True,
        help="Perform a dry run without copying files.",
        is_flag=True,
        show_default=True,
    ),
    cache_file: Path = typer.Option("file_hashes.json", help="Cache file for file hashes."),
    log_level: str = typer.Option("INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)."),
):
    """
    Copies files from SOURCE_DIR to TARGET_DIR, keeping only one copy of duplicates.
    """
    logging.basicConfig(
        level=log_level.upper(),
        format="%(message)s",
        handlers=[RichHandler()]
    )
    progress = Progress(BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TimeRemainingColumn())

    cache = load_cache(cache_file)
    with progress:
        duplicates, unique_files = find_duplicates(source_dir, progress, cache)
    save_cache(cache_file, cache)

    # Calculate summary statistics
    total_duplicate_groups = len(duplicates)
    total_duplicate_files = sum(len(group) for group in duplicates)
    total_redundant_files = sum(len(group) - 1 for group in duplicates)
    total_redundant_size = sum(
        sum(file_info['size'] for file_info in group[1:]) for group in duplicates
    )
    total_files_to_copy = len(unique_files) + total_duplicate_groups
    total_size_to_copy = sum(file_info['size'] for file_info in unique_files) + sum(
        group[0]['size'] for group in duplicates
    )

    # Prepare JSON output
    output_data = {
        'summary': {
            'total_duplicate_groups': total_duplicate_groups,
            'total_duplicate_files': total_duplicate_files,
            'total_redundant_files': total_redundant_files,
            'total_redundant_size_bytes': total_redundant_size,
            'total_files_to_copy': total_files_to_copy,
            'total_size_to_copy_bytes': total_size_to_copy
        },
        'duplicates': duplicates
    }

    with open(output_json, 'w') as f:
        json.dump(output_data, f, indent=4)

    logging.info(f"Duplicate groups saved to {output_json}")

    if not dryrun:
        os.makedirs(target_dir, exist_ok=True)
        copied_files = set()
        task_copy = progress.add_task("[cyan]Copying files...", total=total_files_to_copy)
        # Copy unique files
        for file_info in unique_files:
            src = Path(file_info['path'])
            dst = target_dir / src.relative_to(source_dir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            logging.info(f"Copied {src} to {dst}")
            copied_files.add(src)
            progress.advance(task_copy)

        # Copy one file from each duplicate group
        for group in duplicates:
            src = Path(group[0]['path'])
            dst = target_dir / src.relative_to(source_dir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            logging.info(f"Copied {src} to {dst}")
            copied_files.add(src)
            progress.advance(task_copy)
        logging.info("File copying complete.")
    else:
        logging.info("Dry run complete. No files were copied.")

if __name__ == "__main__":
    app()
