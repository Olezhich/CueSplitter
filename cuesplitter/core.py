import asyncio
from pathlib import Path

from typing import Any, Awaitable, Callable
import cuetools

from cuesplitter.models import Album, Track

from cuesplitter.tags import set_tags

import tempfile

from cuesplitter.ffmpeg import extract_track, join_tracks, get_raw_pcm, cmp_raw_pcm


async def parse_album(cue_path: Path, strict_title_case: bool) -> Album:
    cue_dir = cue_path.parent

    with open(cue_path, 'r') as cue:
        album = await Album.from_album_data(
            cuetools.load(cue, strict_title_case), cue_dir
        )

    return album


async def execute_by_workers(
    queue: list[tuple[Any, ...]],
    handler: Callable[..., Awaitable[Any]],
    num_workers: int,
) -> list[Any]:
    """Executes all tasks in the queue using the specified number of workers. Workers take data from the queue as needed and process it with the specified handlers until the queue is empty."""

    async_queue: asyncio.Queue[tuple[Any] | None] = asyncio.Queue()

    for item in queue:
        await async_queue.put(item)

    output: list[Any] = []

    workers = [
        asyncio.create_task(worker(async_queue, output, handler))
        for _ in range(num_workers)
    ]

    await async_queue.join()
    for _ in range(num_workers):
        await async_queue.put(None)

    await asyncio.gather(*workers)

    return output


async def worker(
    queue: asyncio.Queue[tuple[Any, ...] | None],
    output: list[Any],
    handler: Callable[..., Awaitable[Any]],
) -> None:
    """Coroutine wrapper that allows it to work with an asynchronous queue"""
    while True:
        item = await queue.get()
        try:
            if not item:
                break

            result = await handler(*item)
            output.append(result)
        finally:
            queue.task_done()


async def track_extraction_handler(
    track: Track,
    album: Album,
    output_dir: Path,
    dry: bool,
) -> Path:
    file_name = f'{track.track:02d}'
    if track.title:
        file_name += f' - {track.title.replace("'", "")}.flac'

    output_file = output_dir / file_name

    if not dry:
        await extract_track(track.offset, track.duration, track.file, output_file)
        set_tags(output_file, album, track)

    return (output_file).resolve()


async def split_album(
    cue_path: Path,
    output_dir: Path,
    strict_title_case: bool,
    num_workers: int,
    dry: bool,
    verify: bool,
) -> list[Path]:
    album = await parse_album(cue_path, strict_title_case)

    if not dry:
        output_dir.mkdir(parents=True, exist_ok=True)

    queue = [(track, album, output_dir, dry) for track in album.tracks]

    output_paths: list[Path] = await execute_by_workers(
        queue, track_extraction_handler, num_workers
    )

    output_paths = sorted(output_paths)

    if verify and len(album.tracks) > 0:
        res = await verify_album(output_paths, album.tracks[0].file, num_workers)
        if not res:
            raise RuntimeError('Not bit-perfect')

    return output_paths


async def verify_album(tracks: list[Path], original: Path, num_workers) -> bool:
    result = False

    with (
        tempfile.NamedTemporaryFile(delete=True) as rhs_flac,
        tempfile.NamedTemporaryFile(delete=True) as lhs_raw,
        tempfile.NamedTemporaryFile(delete=True) as rhs_raw,
    ):
        await join_tracks(tracks, Path(rhs_flac.name))

        queue = [
            (original.resolve(), Path(lhs_raw.name).resolve()),
            (Path(rhs_flac.name).resolve(), Path(rhs_raw.name).resolve()),
        ]

        await execute_by_workers(queue, get_raw_pcm, num_workers)

        print('CMP', Path(lhs_raw.name).resolve(), Path(rhs_raw.name).resolve())
        result = await cmp_raw_pcm(
            Path(lhs_raw.name).resolve(), Path(rhs_raw.name).resolve()
        )
        print('RESULT', result)
    return result
