from pathlib import Path
import subprocess
import cuetools

from cuesplitter.models import Album, Track

from mutagen.flac import FLAC
from mutagen.flac import Picture
from mutagen.id3 import PictureType


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
    picture.mime = "image/jpeg"
    picture.desc = "Front Cover"
    with open(cover_path, "rb") as cover:
        picture.data = cover.read()

    f.add_picture(picture)

    f.save()


def split_album(cue_path: Path, output_dir: Path, strict_title_case: bool):
    album = parse_album(cue_path, strict_title_case)

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

        set_tags(output_file, album, track, cue_path.parent / 'Front.jpeg')

        output_paths.append(output_file)

    return output_paths
