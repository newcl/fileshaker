import os
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

def find_unique_extensions(folder_path: str):
    extensions = set()

    # Walk through the directory and subdirectories
    for root, _, files in os.walk(folder_path):
        for file in files:
            # Get the file extension and add it to the set
            ext = os.path.splitext(file)[1].lower()
            if ext:
                extensions.add(ext)

    # Print the sorted list of unique extensions
    if extensions:
        console.print(f"[cyan]Unique file extensions found in {folder_path}:[/cyan]")
        for ext in sorted(extensions):
            console.print(f"[green]{ext}[/green]")
    else:
        console.print("[yellow]No file extensions found.[/yellow]")

@app.command()
def list_extensions(folder: str):
    """
    Finds all unique file extensions in the provided folder and its subdirectories.
    """
    if os.path.isdir(folder):
        find_unique_extensions(folder)
    else:
        console.print("[bold red]Invalid directory path.[/bold red]")

if __name__ == "__main__":
    app()
