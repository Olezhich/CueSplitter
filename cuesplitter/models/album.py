from __future__ import annotations

from pathlib import Path
from cuetools import TrackData, AlbumData

from cuesplitter.ffmpeg import get_duration


class Track(TrackData):
    duration: float  # in seconds
    offset: float  # in seconds

    model_config = {'frozen': True}

    @classmethod
    def from_track_data(
        cls, track: TrackData, base_dir: Path, duration: float, offset: float
    ) -> Track:
        parent = track.model_dump()
        parent['file'] = (base_dir / parent['file']).resolve()

        return cls(duration=duration, offset=offset, **parent)


class Album(AlbumData):
    tracks: list[Track]  # type: ignore

    @classmethod
    async def from_album_data(cls, album: AlbumData, base_dir: Path) -> Album:
        tracks = []
        duration: float
        offset: float | None = None
        for track_cue in sorted(album.tracks, reverse=True, key=lambda x: x.track):
            offset, duration = await _get_offset_duration(
                str(base_dir), track_cue, offset
            )
            tracks.append(Track.from_track_data(track_cue, base_dir, duration, offset))

        parent = album.model_dump()
        parent['tracks'] = tracks

        return cls(**parent)


async def _get_offset_duration(
    current_dir: str, track_cue: TrackData, next_offset: float | None
) -> tuple[float, float]:
    offset = 0.0
    if track_cue.index00 is not None:
        offset = track_cue.index00.seconds
    elif track_cue.index01 is not None:
        offset = track_cue.index01.seconds
    duration = (
        next_offset - offset
        if next_offset is not None
        else await get_audiofile_duration(current_dir / track_cue.file) - offset
    )
    return offset, duration


async def get_audiofile_duration(path_to_file: Path) -> float:
    return await get_duration(path_to_file)
