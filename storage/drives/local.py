from pathlib import Path
from django.conf import settings

from storage.utils import generate_breadcrumbs, path_attr


def list_files(path):
    local_root = settings.LOCALE_STORAGE_PATH
    full_path = Path(local_root).joinpath(path)
    walk_dirs = [i for i in full_path.iterdir()]
    files = [file for file in walk_dirs if file.is_file()]
    return files


def delete_file(path):
    file = Path(path)
    if file.exists():
        if file.is_file():
            file.unlink()
            return True
        else:
            try:
                file.rmdir()
                return True
            except OSError:
                return False
    return False


def get_context(drive, path):
    root = Path(settings.LOCALE_STORAGE_PATH, drive.root)
    full_path = root.joinpath(path[1::])
    if path == '/':
        full_path = root
    walk_files = [i for i in full_path.iterdir()]
    readme = False
    for file in walk_files:
        if file.name.lower() == 'readme.md':
            readme = file.read_text(encoding='utf8')
    context = {
        'drive_id': drive.id,
        'drive_slug': drive.slug,
        'breadcrumbs': generate_breadcrumbs(drive.slug, path),
        'files': [path_attr(drive.slug, root, i) for i in walk_files],
        'readme': readme,
    }
    return context
