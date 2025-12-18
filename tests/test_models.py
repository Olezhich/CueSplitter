from pathlib import Path
from unittest.mock import patch
import cuetools  # type: ignore

from cuesplitter.models.album import Album


def test_duration(cue_sample_for_durations):
    with patch(
        'cuesplitter.models.album.get_audiofile_duration', return_value=28.0 * 60
    ):
        album = Album.from_album_data(
            cuetools.loads(cue_sample_for_durations, True), Path('/music/scorpions')
        )

    for track in album.tracks:
        print(track)

    assert all(track.duration == 4 * 60 for track in album.tracks)
