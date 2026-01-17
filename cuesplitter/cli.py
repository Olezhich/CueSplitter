from pathlib import Path
from cuesplitter.core import split_album, verify_album

from cuetools import CueParseError, CueValidationError

import typer

from rich.console import Console

import asyncio

import time


app = typer.Typer()

stdout = Console()
stderr = Console(stderr=True)


@app.command()
def split(
    input: Path,
    output: Path = Path(),
    strict: bool = False,
    dry: bool = False,
    verify: bool = False,
    workers: int = 1,
    timer: bool = False,
):
    """
    Split album on different tracks by `.cue` file
    """
    t1 = time.time()

    try:
        result = asyncio.run(split_album(input, output, strict, workers, dry, verify))

        out = sorted(result)
        for path in out:
            stdout.print(path, end='\0')
    except CueValidationError as e:
        stderr.print('[bold red]Cue validation error:[/bold red]')
        stderr.print(str(e))
        raise typer.Exit(code=1)
    except CueParseError as e:
        stderr.print('[bold red]Cue parse error:[/bold red]')
        stderr.print(str(e))
        raise typer.Exit(code=1)
    except RuntimeError as e:
        stderr.print('[bold red]Runtime error:[/bold red]')
        stderr.print(str(e))
        raise typer.Exit(code=1)
    if timer:
        t2 = time.time()
        stdout.print(f'[bold green]{(t2 - t1)}[/bold green]')


# @app.command()
# def join(
#     tracks: list[Path],
#     output: Path = Path('joined.flac'),
# ):
#     """
#     Join tracks  into a single album file
#     """
#     if not tracks:
#         stderr.print('Error: No input tracks provided.')
#         raise typer.Exit(1)

#     for p in tracks:
#         if not p.exists():
#             stderr.print(f'Error: File not found: {p}')
#             raise typer.Exit(1)

#     join_album(tracks, output)


@app.command()
def verify(original: Path, tracks: list[Path], workers: int = 1):
    """Verify album split"""
    if not tracks:
        stderr.print('Error: No input tracks provided.')
        raise typer.Exit(1)

    for p in tracks:
        if not p.exists():
            stderr.print(f'Error: File not found: {p}')
            raise typer.Exit(1)

    stdout.print(asyncio.run(verify_album(tracks, original, workers)))


if __name__ == '__main__':
    app()
