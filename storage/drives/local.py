from pathlib import Path
from django.conf import settings


def list_files(path):
    local_root = settings.LOCALE_STORAGE_PATH
    full_path = Path(local_root).joinpath(path)
    walk_dirs = [i for i in full_path.iterdir()]
    files = [file for file in walk_dirs if file.is_file()]
    return files

