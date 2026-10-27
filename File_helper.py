import json
import os
import tempfile
from pathlib import Path


class FileHelper:
    """Read and write the movie/ticket data file."""

    def save(self, path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".tmp",
                                             dir=path.parent, delete=False) as file:
                temporary_path = Path(file.name)
                json.dump(data, file, ensure_ascii=False, indent=2)
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def load(self, path):
        try:
            with Path(path).open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError("Data file is not valid JSON") from error
