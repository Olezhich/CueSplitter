from pathlib import Path
import subprocess
import cuetools

from cuesplitter.models import Album, Track

from mutagen.flac import FLAC
from mutagen.flac import Picture
from mutagen.id3 import PictureType

import tempfile


def parse_album(cue_path: Path, strict_title_case: bool) -> Album:
    cue_dir = cue_path.parent

    with open(cue_path, 'r') as cue:
        album = Album.from_album_data(cuetools.load(cue, strict_title_case), cue_dir)

    return album


def set_tags(track_path: Path, album: Album, track: Track, cover_path: Path) -> None:
    """add vorbis commets"""
    f = FLAC(track_path)

    f.clear()
    f.clear_pictures()

    if album.title:
        f['ALBUM'] = album.title
    if album.performer:
        f['ARTIST'] = album.performer
    if album.rem.date:
        f['DATE'] = str(album.rem.date)
    if album.rem.genre:
        f['GENRE'] = album.rem.genre

    if track.performer:
        f['PERFORMER'] = track.performer
    if track.title:
        f['TITLE'] = track.title
    f['TRACKNUMBER'] = f'{track.track:02d}'

    picture = Picture()
    picture.type = PictureType.OTHER
    picture.mime = 'image/jpeg'
    picture.desc = 'Front Cover'
    with open(cover_path, 'rb') as cover:
        picture.data = cover.read()

    f.add_picture(picture)

    f.save()


def split_album(cue_path: Path, output_dir: Path, strict_title_case: bool, dry: bool):
    album = parse_album(cue_path, strict_title_case)

    if not dry:
        output_dir.mkdir(parents=True, exist_ok=True)

    output_paths = []
    for track in album.tracks:
        file_name = f'{track.track:02d}'
        if track.title:
            file_name += f' - {track.title.replace("'", "")}.flac'

        output_file = output_dir / file_name

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
        if not dry:
            result = subprocess.run(cmd, stderr=subprocess.PIPE)

            if result.returncode != 0:
                raise RuntimeError(f'ffmpeg failed with copy: {result.stderr.decode()}')

            set_tags(output_file, album, track, cue_path.parent / 'Front.jpeg')

        output_paths.append((output_file).resolve())

    return output_paths


def join_album(tracks: list[Path], output: Path) -> None:
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for p in tracks:
            safe_path = p.resolve().as_posix()
            f.write(f"file '{safe_path}'\n")
        filelist = f.name
    try:
        cmd = [
            'ffmpeg',
            '-f',
            'concat',
            '-safe',
            '0',
            '-i',
            filelist,
            '-c:a',
            'flac',
            '-f',
            'flac',
            str(output.resolve()),
            '-y',
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f'ffmpeg failed:\n{result.stderr.decode()}')
    finally:
        Path(filelist).unlink()
