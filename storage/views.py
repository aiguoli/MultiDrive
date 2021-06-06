from pathlib import PurePath, Path

import requests
from apscheduler.triggers.interval import IntervalTrigger
from django.contrib.auth.decorators import login_required
from django.http import FileResponse

from .models import Drive, Category
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.urls import reverse

from .drives import onedrive, aliyundrive
from .utils import od_path_attr, ali_path_attr, file_type, get_aliyundrive_filename, generate_breadcrumbs, path_attr
from .timer import scheduler, refresh_onedrive_token_by_id, refresh_aliyundrive_token_by_id

scheduler.start()


def index(request):
    return render(request, 'storage/index.html')


def disks(request):
    # list all storage you added
    drives = Drive.objects.all()
    context = {
        'drives': drives
    }
    return render(request, 'storage/disks.html', context)


# Authentication start
@login_required
def add_disk(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        cate = Category.objects.filter(name=category).first()
        slug = request.POST.get('display_name')
        if category == 'onedrive':
            client_id = request.POST.get('client_id')
            client_secret = request.POST.get('client_secret')
            if cate is None:
                return redirect(reverse('storage:add_disk'))
            one = Drive(name=name, client_id=client_id, client_secret=client_secret, slug=slug)
            one.category = cate
            one.save()
            request.session['onedrive_id'] = one.id
            request.session['client_id'] = client_id
            request.session['client_secret'] = client_secret
            redirect_uri = request.build_absolute_uri(reverse('storage:callback'))
            if settings.DEBUG:
                redirect_uri = 'http://localhost:8000/callback'
            authenticate_url = onedrive.get_login_code(client_id=client_id, redirect_uri=redirect_uri)
            return redirect(authenticate_url)
        elif category == 'aliyun':
            refresh_token = request.POST.get('refresh_token')
            tokens = aliyundrive.refresh_token(refresh_token)
            user_info = aliyundrive.get_user_info(token=tokens.get('access_token'))
            ali = Drive(name=name, access_token=tokens.get('access_token'), refresh_token=tokens.get('refresh_token'),
                        client_id=user_info.get('default_drive_id'), slug=slug)
            ali.category = cate
            ali.save()
            scheduler.add_job(
                refresh_aliyundrive_token_by_id,
                trigger=IntervalTrigger(seconds=3600),
                id='refresh_aliyundrive_token_every_3600s',
                args=(ali.id,)
            )
        elif category == 'local':
            drive = Drive(name=name, root=settings.LOCALE_STORAGE_PATH, slug=slug)
            drive.category = cate
            drive.save()
        return redirect(reverse('storage:disks'))
    context = {
        'categories': categories
    }
    return render(request, 'storage/add_disk.html', context)


def callback(request):
    code = request.GET.get('code')
    client_id = request.session.get('client_id')
    client_secret = request.session.get('client_secret')
    tokens = onedrive.get_login_token(code=code, client_id=client_id, client_secret=client_secret)
    one = get_object_or_404(Drive, pk=request.session.get('onedrive_id'))
    one.access_token = tokens.get('access_token')
    one.refresh_token = tokens.get('refresh_token')
    one.save()
    scheduler.add_job(
        refresh_onedrive_token_by_id,
        trigger=IntervalTrigger(seconds=1800),
        id='refresh_onedrive_token_every_1800s',
        args=(one.id,)
    )
    return redirect(reverse('storage:disks'))


def refresh(request, drive_id):
    refresh_onedrive_token_by_id(drive_id)
    return redirect(reverse('filemanager:index'))


# File operation
def list_files(request, drive_slug, path=''):
    if 'preview' in request.GET:
        return preview(request, path, drive_slug)
    drive = Drive.objects.filter(slug=drive_slug).first()
    category = drive.category.name.lower()

    if category == 'onedrive':
        full_path = str(PurePath(drive.root, path))
        # judge folder or file
        item = onedrive.get_file(token=drive.access_token, path=full_path)
        if item.get('file'):
            return redirect(item.get('@microsoft.graph.downloadUrl'))

        results = onedrive.list_files(token=drive.access_token, path=full_path).get('value')
        files = [od_path_attr(i, drive_slug, path) for i in results if i.get('file')]
        dirs = [od_path_attr(j, drive_slug, path) for j in results if j.get('folder')]
        readme = None
        for file in files:
            if file.get('name').lower() == 'readme.md':
                response = requests.get(file.get('download_url'))
                response.encoding = 'utf-8'
                readme = response.text
        context = {
            'breadcrumbs': generate_breadcrumbs(drive_slug, path),
            'dirs': dirs,
            'files': files,
            'readme': readme
        }
        return render(request, 'storage/list.html', context)
    elif category == 'aliyun':
        if path == '':
            path = 'root'
        results = aliyundrive.list_files(token=drive.access_token, drive_id=drive.client_id, path=path)
        if results is None:
            result = aliyundrive.get_download_url(token=drive.access_token, drive_id=drive.client_id, file_id=path)
            return redirect(result.get('url'), Referer='https://www.aliyundrive.com/')
        dirs = [ali_path_attr(i, drive_slug, i.get('file_id')) for i in results if i.get('type') == 'folder']
        files = [ali_path_attr(j, drive_slug, j.get('file_id')) for j in results if j.get('type') == 'file']
        readme = None
        for file in files:
            if file.get('name').lower == 'readme.md':
                readme = requests.get(file.get('download_url')).text
        context = {
            'root': reverse('storage:index'),
            'dirs': dirs,
            'files': files,
            'readme': readme,
        }
        return render(request, 'storage/list.html', context)
    elif category == 'local':
        root = Path(settings.LOCALE_STORAGE_PATH, drive.root)
        full_path = root / path

        if full_path.is_file():
            if 'preview' in request.GET:
                return preview(request, drive_slug, path)
            return download(request, full_path)
        walk_dirs = [i for i in full_path.iterdir()]
        files = [file for file in walk_dirs if file.is_file()]
        readme = False
        for file in files:
            if file.name.lower() == 'readme.md':
                readme = file.read_text(encoding='utf8')
        context = {
            'breadcrumbs': generate_breadcrumbs(drive_slug, path),
            'dirs': [path_attr(root, drive_slug, i) for i in walk_dirs if i.is_dir()],
            'files': [path_attr(root, drive_slug, j) for j in files],
            'readme': readme
        }
        return render(request, 'storage/list.html', context)


def preview(request, path, drive_slug):
    drive = Drive.objects.filter(slug=drive_slug).first()
    full_path = str(PurePath(drive.root, path))
    category = drive.category.name.lower()
    context = {}
    if category == 'onedrive':
        result = onedrive.get_file(token=drive.access_token, path=full_path)
        name = result.get('name')
        prefix = file_type(name.split('.')[-1])
        context = {
            'breadcrumbs': generate_breadcrumbs(drive_slug, path),
            'name': name,
            'file_type': prefix
        }
    elif category == 'aliyun':
        result = aliyundrive.get_download_url(token=drive.access_token, drive_id=drive.client_id, file_id=path)
        url = result.get('url')
        name = get_aliyundrive_filename(url)
        prefix = file_type(name.split('.')[-1])
        context = {
            'root': path,
            'name': name,
            'file_type': prefix
        }
    elif category == 'local':
        local_path = Path(settings.LOCALE_STORAGE_PATH, drive.root)
        file_path = local_path / path
        prefix = file_path.suffix.replace('.', '')
        context = {
            'breadcrumbs': generate_breadcrumbs(drive_slug, path),
            'name': file_path.name,
            'file_type': file_type(prefix)
        }
    return render(request, 'storage/preview.html', context=context)


def download(request, path):
    # download local file
    file = open(path, 'rb')
    response = FileResponse(file)
    return response
