from pathlib import Path

from cuesplitter.models import Album, Track

from mutagen.flac import FLAC


def set_tags(track_path: Path, album: Album, track: Track) -> None:
    """add vorbis commets"""
    f = FLAC(track_path)

    f.clear()
    f.clear_pictures()

    # Album info
    if album.title:
        f['ALBUM'] = album.title
    if album.performer:
        f['ARTIST'] = album.performer
        f['PERFORMER'] = album.performer
    if album.rem.date:
        f['DATE'] = str(album.rem.date)
    if album.rem.genre:
        f['GENRE'] = album.rem.genre
    if album.rem.replaygain_gain:
        f['REPLAYGAIN_ALBUM_GAIN'] = f'{album.rem.replaygain_gain:.2f} dB'
    if album.rem.replaygain_peak:
        f['REPLAYGAIN_ALBUM_PEAK'] = f'{album.rem.replaygain_peak:.6f}'

    # Track info
    if track.performer:
        f['ARTIST'] = track.performer
        f['PERFORMER'] = track.performer
    if track.title:
        f['TITLE'] = track.title
    f['TRACKNUMBER'] = f'{track.track:02d}'
    if track.rem.replaygain_gain:
        f['REPLAYGAIN_TRACK_GAIN'] = f'{track.rem.replaygain_gain:.2f} dB'
    if track.rem.replaygain_peak:
        f['REPLAYGAIN_TRACK_PEAK'] = f'{track.rem.replaygain_peak:.6f}'

    f.save()
