import asyncio
from pathlib import Path
import subprocess
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


async def track_extraction_handler(
    queue: asyncio.Queue[tuple[Track, Album, Path] | None],
    output_dir: Path,
    output: list[Path],
    dry: bool,
) -> None:
    while True:
        item = await queue.get()
        try:
            if not item:
                break

            track, album, cue_dir = item

            file_name = f'{track.track:02d}'
            if track.title:
                file_name += f' - {track.title.replace("'", "")}.flac'

            output_file = output_dir / file_name

            if not dry:
                await extract_track(
                    track.offset, track.duration, track.file, output_file
                )
                set_tags(output_file, album, track)

            output.append((output_file).resolve())
        finally:
            queue.task_done()


async def split_album(
    cue_path: Path,
    output_dir: Path,
    strict_title_case: bool,
    num_workers: int,
    dry: bool,
    verify: bool,
) -> list[Path]:
    album = await parse_album(cue_path, strict_title_case)
    cue_dir = cue_path.parent

    if not dry:
        output_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[Path] = []

    queue: asyncio.Queue[tuple[Track, Album, Path] | None] = asyncio.Queue()

    for track in album.tracks:
        await queue.put((track, album, cue_dir))

    workers = [
        asyncio.create_task(
            track_extraction_handler(queue, output_dir, output_paths, dry)
        )
        for _ in range(num_workers)
    ]

    await queue.join()

    for _ in range(num_workers):
        await queue.put(None)

    await asyncio.gather(*workers)

    output_paths = sorted(output_paths)

    if verify and len(album.tracks) > 0:
        res = await verify_album(output_paths, album.tracks[0].file, num_workers)
        if not res:
            raise RuntimeError('Not bit-perfect')

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


async def raw_pcm_handler(queue: asyncio.Queue[tuple[Path, Path] | None]) -> None:
    while True:
        item = await queue.get()
        try:
            if not item:
                break

            input, output = item

            await get_raw_pcm(input, output)
        finally:
            queue.task_done()


async def verify_album(tracks: list[Path], original: Path, num_workers) -> bool:
    result = False

    with (
        tempfile.NamedTemporaryFile(delete=True) as rhs_flac,
        tempfile.NamedTemporaryFile(delete=True) as lhs_raw,
        tempfile.NamedTemporaryFile(delete=True) as rhs_raw,
    ):
        await join_tracks(tracks, Path(rhs_flac.name))

        queue: asyncio.Queue[tuple[Path, Path] | None] = asyncio.Queue()

        await queue.put((original.resolve(), Path(lhs_raw.name).resolve()))
        await queue.put((Path(rhs_flac.name).resolve(), Path(rhs_raw.name).resolve()))

        print(
            'QUEUE',
            (original.resolve(), Path(lhs_raw.name).resolve()),
            (Path(rhs_flac.name).resolve(), Path(rhs_raw.name).resolve()),
        )

        workers = [
            asyncio.create_task(raw_pcm_handler(queue)) for _ in range(num_workers)
        ]

        await queue.join()

        for _ in range(num_workers):
            await queue.put(None)

        await asyncio.gather(*workers)
        print('CMP', Path(lhs_raw.name).resolve(), Path(rhs_raw.name).resolve())
        result = await cmp_raw_pcm(
            Path(lhs_raw.name).resolve(), Path(rhs_raw.name).resolve()
        )
        print('RESULT', result)
    return result
