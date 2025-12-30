from pathlib import Path

import asyncio


async def get_duration(audio_file: Path) -> float:
    cmd = [
        'ffprobe',  # Call ffprobe
        '-v',
        'error',  # Log level: errors
        '-show_entries',
        'format=duration',  # Print only duration
        '-of',
        'default=nw=1:nokey=1',  # Without separators, etc.
        f'{audio_file}',
    ]

    sub_proccess = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    result, _ = await sub_proccess.communicate()

    if sub_proccess.returncode != 0:
        raise RuntimeError(f'Cant proccess {audio_file} audio file duration')

    try:
        return float(result.decode().strip())
    except ValueError:
        raise RuntimeError(f'Cant proccess {audio_file} audio file duration')


async def extract_track(
    offset: float, duration: float, input: Path, output: Path
) -> None:
    cmd = [
        'ffmpeg',  # Call ffmpeg
        '-ss',
        str(offset),  # Start time
        '-t',
        str(duration),  # Duration
        '-i',
        str(input),  # Input file
        '-c:a',
        'flac',  # Write the result into flac
        str(output),  # Output file
        '-y',  # Overwrite the output file if it already exists
    ]

    sub_proccess = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    await sub_proccess.communicate()

    if sub_proccess.returncode != 0:
        raise RuntimeError(
            f'Cant extract tarck from {input} audio file. Offset: {offset}, duration: {duration}'
        )
