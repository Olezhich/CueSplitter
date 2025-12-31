from pathlib import Path

import asyncio


async def run_cmd(cmd: list[str]) -> str:
    sub_proccess = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    result, _ = await sub_proccess.communicate()

    if sub_proccess.returncode != 0:
        raise RuntimeError()

    return result.decode().strip()


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
        '-f'  # Output format
        f's{bit_depth}le',
        '-acodec',  # Audio codec
        f'pcm_s{bit_depth}le',
        '-',  # Output to stdout
        '>',  # Redirect to output file
        str(output),
    ]

    try:
        await run_cmd(cmd)
    except RuntimeError:
        raise RuntimeError(f'Cant get raw pcm from {input} audio file')
