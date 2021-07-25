from pathlib import PurePosixPath, Path

from django.conf import settings
from django.shortcuts import get_object_or_404

from storage.models import Drive, File
from storage.drives import onedrive, aliyundrive, local, baidudisk


def list_files(drive_id, absolute_path):
    drive = get_object_or_404(Drive, pk=drive_id)
    category = drive.category.name.lower()
    new_files = None
    posix_absolute_path = PurePosixPath(absolute_path)
    if category == 'onedrive':
        files = onedrive.list_files(drive.access_token, absolute_path)
        if files:
            new_files = onedrive.save_files_to_db(files, drive_id)
    elif category == 'aliyun':
        absolute_path = PurePosixPath(absolute_path)
        parent = File.objects.filter(parent_path=posix_absolute_path.parent,
                                     drive_id=drive.id,
                                     name=posix_absolute_path.name).first()
        files = aliyundrive.list_files(drive.access_token, drive_id=drive.client_id,
                                       parent_file_id=parent.file_id if parent else 'root')
        if files:
            new_files = aliyundrive.save_files_to_db(files, drive_id, absolute_path)
    elif category == 'baidu':
        parent = File.objects.filter(parent_path=posix_absolute_path.parent,
                                     drive_id=drive.id,
                                     name=posix_absolute_path.name).first()
        files = baidudisk.list_files(drive.access_token, path=absolute_path)
        if files:
            new_files = baidudisk.save_files_to_db(files, drive_id, absolute_path, parent.id if parent else None)
    return new_files


def delete_file(drive_id, file_id):
    drive = get_object_or_404(Drive, pk=drive_id)
    file = File.objects.filter(file_id=file_id)
    category = drive.category.name.lower()
    res = None
    if category == 'onedrive':
        res = onedrive.delete_file(drive.access_token, path=file.parent_path+file.name)
    elif category == 'aliyun':
        res = aliyundrive.temporarily_delete_file(drive.access_token, drive_id=drive.id, file_id=file_id)
    elif category == 'local':
        local.delete_file(Path(settings.LOCALE_STORAGE_PATH, drive.root, file_id))
    if res == 204:
        return file.delete()
    return False
