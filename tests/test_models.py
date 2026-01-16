import asyncio
from pathlib import Path
from unittest.mock import patch
import cuetools

from cuesplitter.models.album import Album

from .conftest import mock_durations


def test_duration(cue_sample_for_durations):
    with patch(
        'cuesplitter.models.album.get_audiofile_duration',
        side_effect=lambda x: mock_durations[x],
    ):
        album = asyncio.run(
            Album.from_album_data(
                cuetools.loads(cue_sample_for_durations, True), Path('/music/scorpions')
            )
        )

    for track in album.tracks:
        print(track)

    assert all(track.duration == 4 * 60 for track in album.tracks)
