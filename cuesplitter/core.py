from pathlib import Path
import subprocess
import cuetools

from cuesplitter.models import Album


def parse_album(cue_path: Path) -> Album:
    cue_dir = cue_path.parent

    with open(cue_path, 'r') as cue:
        album = Album.from_album_data(cuetools.load(cue), cue_dir)

    return album


def split_album(cue_path: Path, output_dir: Path):
    album = parse_album(cue_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths = []
    for track in album.tracks:
        output_file = output_dir / f'{track.track:02d} - {track.title}.flac'

        cmd = [
            'ffmpeg',
            '-ss',
            str(track.offset),
            '-t',
            str(track.duration),
            '-i',
            str(track.file),
            '-c:a',
            'flac',
            str(output_file),
            '-y',
        ]
        result = subprocess.run(cmd, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f'ffmpeg failed with copy: {result.stderr.decode()}')

        output_paths.append(output_file)

    return output_paths
