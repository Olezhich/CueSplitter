from pathlib import Path
from cuesplitter.core import split_album, parse_album

import typer


def split(input: Path, output: Path = Path(), dry: bool = False):
    """
    Split album on different tracks by `.cue` file
    """
    if dry:
        album = parse_album(input)
        for track in album.tracks:
            print(track)
    else:
        split_album(input, output)


if __name__ == '__main__':
    typer.run(split)
