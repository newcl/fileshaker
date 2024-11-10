import typer
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def hash_file(file_path):
    """Returns the SHA-256 hash of the file's contents."""
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024*8), b""):
                hasher.update(chunk)
        return file_path, hasher.hexdigest()
    except Exception as e:
        console.print(f"[red]Error reading file {file_path}: {e}[/red]")
        return file_path, None

def dedupe(folder: str, dry_run: bool = False, num_threads: int = 4):
    """
    Deduplicates files in the provided folder by removing duplicates based on content.
    Only one instance of each duplicated file is kept.

    Parameters:
    folder: str - The path to the folder to deduplicate.
    dry_run: bool - If set, only displays duplicates without deleting them.
    num_threads: int - Number of threads to use for file processing.
    """
    if not os.path.isdir(folder):
        console.print("[bold red]Provided path is not a directory.[/bold red]")
        raise typer.Exit()

    console.print(f"[cyan]Scanning folder: [bold]{folder}[/bold][/cyan]")

    seen_hashes = {}
    duplicates = []
    file_paths = []

    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                file_paths.append(file_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Hashing files...", total=len(file_paths))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_path = {executor.submit(hash_file, path): path for path in file_paths}

            for future in as_completed(future_to_path):
                path, file_hash = future.result()
                progress.update(task, advance=1)

                if file_hash:
                    if file_hash in seen_hashes:
                        duplicates.append(path)
                    else:
                        seen_hashes[file_hash] = path

    # Display duplicates in a table
    if duplicates:
        table = Table(title="Duplicate Files")
        table.add_column("File Path", style="magenta")

        for dup in duplicates:
            table.add_row(dup)

        console.print(table)

        if dry_run:
            console.print(f"[yellow]Dry-run complete. {len(duplicates)} duplicate(s) found.[/yellow]")
        else:
            for dup in duplicates:
                os.remove(dup)
                console.print(f"[green]Removed duplicate:[/green] {dup}")

            console.print(f"[green]Deduplication complete. {len(duplicates)} duplicate(s) removed.[/green]")
    else:
        console.print("[green]No duplicates found.[/green]")

if __name__ == "__main__":
    typer.run(dedupe)
