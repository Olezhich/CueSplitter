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
