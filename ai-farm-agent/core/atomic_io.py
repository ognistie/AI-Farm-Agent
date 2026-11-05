"""Bounded recovery for Windows sharing violations; old data stays intact on failure."""
import os
import time


def replace_file(source, destination, attempts=10):
    for attempt in range(attempts):
        try:
            os.replace(source, destination)
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt + 1 == attempts:
                raise
            time.sleep(min(0.025 * (attempt + 1), 0.15))
