from pathlib import Path

import asyncio
import tempfile


async def run_cmd_raw(cmd: list[str]) -> bytes:
    sub_proccess = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    result, _ = await sub_proccess.communicate()

    if sub_proccess.returncode != 0:
        raise RuntimeError()

    return result


async def run_cmd(cmd: list[str]) -> str:
    res = await run_cmd_raw(cmd)
    return res.decode().strip()


async def get_duration(audio_file: Path) -> float:
    cmd = [
        'ffprobe',  # Call ffprobe
        '-v',
        'error',  # Log level: errors
        '-show_entries',  # Specify the fields to extract
        'format=duration',  # Print only duration
        '-of',
        'default=nw=1:nokey=1',  # Without separators, etc.
        str(audio_file),
    ]

    try:
        return float(await run_cmd(cmd))
    except (RuntimeError, ValueError):
        raise RuntimeError(f'Cant proccess {audio_file} audio file duration')


async def get_bit_depth(audio_file: Path) -> float:
    cmd = [
        'ffprobe',  # Call ffprobe
        '-v',
        'error',  # Log level: errors
        '-show_entries',  # Specify the fields to extract
        'stream=bits_per_raw_sample',  # Get the bits_per_raw_sample from STREAMINFO
        '-of',
        'default=nw=1:nokey=1',  # Without separators, etc.
        str(audio_file),
    ]
    try:
        return int(await run_cmd(cmd))
    except (ValueError, RuntimeError):
        raise RuntimeError(f'Cant proccess {audio_file} audio file bit depth')


async def extract_track(
    offset: float, duration: float, input: Path, output: Path
) -> None:
    cmd = [
        'ffmpeg',  # Call ffmpeg
        '-ss',  # Start time
        str(offset),
        '-t',  # Duration
        str(duration),
        '-i',  # Input file
        str(input),
        '-c:a',
        'flac',  # Write the result into flac
        str(output),  # Output file
        '-y',  # Overwrite the output file if it already exists
    ]

    try:
        await run_cmd(cmd)
    except RuntimeError:
        raise RuntimeError(
            f'Cant extract tarck from {input} audio file. Offset: {offset}, duration: {duration}'
        )


async def join_tracks(tracks: list[Path], output: Path) -> None:
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for p in tracks:
            safe_path = p.resolve().as_posix()
            f.write(f"file '{safe_path}'\n")
        filelist = f.name

    cmd = [
        'ffmpeg',  # Call ffmpeg
        '-f',
        'concat',
        '-safe',
        '0',  # Disable concat safe mode
        '-i',  # Input file
        filelist,
        '-c:a',
        'flac',  # Write the result into flac
        '-f',  # Output format
        'flac',
        str(output.resolve()),
        '-y',  # Overwrite the output file if it already exists
    ]
    try:
        await run_cmd(cmd)
    except RuntimeError:
        raise RuntimeError(f'Cant join tracks into file: {output}')

    finally:
        Path(filelist).unlink()

    print('join_tracks DONE')


async def get_raw_pcm(input: Path, output: Path) -> None:
    try:
        bit_depth = await get_bit_depth(input)
    except RuntimeError:
        bit_depth = 32

    bit_depth = bit_depth if bit_depth in [16, 24, 32] else 32

    cmd = [
        'ffmpeg',  # Call ffmpeg
        '-i',  # Input file
        str(input),
        '-f',  # Output format
        f's{bit_depth}le',
        '-acodec',  # Audio codec
        f'pcm_s{bit_depth}le',
        '-',  # Output to stdout
    ]

    try:
        pcm = await run_cmd_raw(cmd)
    except RuntimeError:
        raise RuntimeError(f'Cant get raw pcm from {input} audio file')

    with open(output, 'wb') as f:
        f.write(pcm)

    print('get_raw_pcm DONE')


async def cmp_raw_pcm(lhs: Path, rhs: Path) -> bool:
    print_file_sizes_exact(lhs, rhs)
    cmd = [
        'cmp',
        str(lhs),
        str(rhs),
    ]
    try:
        res = await run_cmd(cmd)
        print('cmp_raw_pcm DONE\n', res)
    except RuntimeError:
        return False
    return True


def print_file_sizes_exact(lhs: Path, rhs: Path) -> None:
    """Print exact file sizes in bytes."""

    def size_or_error(p: Path) -> str:
        return f'{p.stat().st_size} bytes' if p.exists() else 'NOT FOUND'

    print(f'lhs: {lhs} → {size_or_error(lhs)}')
    print(f'rhs: {rhs} → {size_or_error(rhs)}')
