from pathlib import Path
import subprocess
import cuetools

from cuesplitter.models import Album


def split_album(cue_path: Path, output_dir: Path):
    cue_dir = cue_path.parent

    with open(cue_path, 'r') as cue:
        try:
            album = Album.from_album_data(cuetools.load(cue), cue_dir)
        except (cuetools.CueParseError, cuetools.CueValidationError) as e:
            raise e

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
