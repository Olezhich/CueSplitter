from pathlib import Path
from cuesplitter.core import split_album, parse_album

from cuetools import CueParseError, CueValidationError

import typer

from rich.console import Console


app = typer.Typer()

stdout = Console()
stderr = Console(stderr=True)


@app.command()
def split(input: Path, output: Path = Path(), strict: bool = False, dry: bool = False):
    """
    Split album on different tracks by `.cue` file
    """
    try:
        if dry:
            album = parse_album(input, strict)
            for track in album.tracks:
                stdout.print(track)
        else:
            split_album(input, output, strict)
    except CueValidationError as e:
        stderr.print('[bold red]Cue validation error:[/bold red]')
        stderr.print(str(e))
        raise typer.Exit(code=1)
    except CueParseError as e:
        stderr.print('[bold red]Cue parse error:[/bold red]')
        stderr.print(str(e))
        raise typer.Exit(code=1)


if __name__ == '__main__':
    app()
