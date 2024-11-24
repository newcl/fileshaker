import os
import hashlib
import typer
from pathlib import Path
from rich.console import Console
from rich.progress import track

app = typer.Typer()
console = Console()

def hash_first_4k(file_path):
    """Calculates the SHA-256 hash of the first 4 KB of the given file."""
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            chunk = f.read(4096)  # Read the first 4 KB of the file
            hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        console.print(f"[red]Error processing {file_path}: {e}[/red]")
        return None

@app.command()
def hash_files_in_folder(folder: str):
    """
    Calculates the SHA-256 hash of the first 4 KB of each file in the specified folder.
    
    Parameters:
    folder: str - The path to the folder containing the files to hash.
    """
    folder_path = Path(folder)

    if not folder_path.is_dir():
        console.print("[bold red]The provided path is not a valid directory.[/bold red]")
        raise typer.Exit()

    console.print(f"[cyan]Calculating SHA-256 hash of the first 4 KB for files in {folder_path}[/cyan]")

    for file_path in track(folder_path.rglob('*'), description="Processing files..."):
        if file_path.is_file():
            hash_value = hash_first_4k(file_path)
            if hash_value:
                console.print(f"{file_path}: [green]{hash_value}[/green]")

if __name__ == "__main__":
    app()
