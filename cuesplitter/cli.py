from pathlib import Path
from cuesplitter.core import split_album

import typer


def split(input: Path, output: Path = Path()):
    """
    Split album on different tracks by `.cue` file
    """
    split_album(input, output)


if __name__ == '__main__':
    typer.run(split)
