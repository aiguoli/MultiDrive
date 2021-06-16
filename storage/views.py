from pathlib import PurePath, Path

from apscheduler.triggers.interval import IntervalTrigger
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.core.cache import cache

from .drives import onedrive, aliyundrive, local
from .models import Drive, Category
from .utils import file_type, get_aliyundrive_filename, generate_breadcrumbs
from .task import scheduler, refresh_onedrive_token_by_id, refresh_aliyundrive_token_by_id

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
            ali_refresh_token = request.POST.get('refresh_token')
            tokens = aliyundrive.refresh_token(ali_refresh_token)
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


def tutorial(request):
    return render(request, 'storage/tutorial.html')


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


@login_required
def refresh_token(request, drive_id):
    drive = get_object_or_404(Drive, pk=drive_id)
    category = drive.category.name.lower()
    if category == 'onedrive':
        refresh_onedrive_token_by_id(drive_id)
    elif category == 'aliyun':
        refresh_aliyundrive_token_by_id(drive_id)
    return redirect(request.META.get('HTTP_REFERER'))


# File operation
def list_files(request, drive_slug, path=''):
    if 'preview' in request.GET:
        return preview(request, path, drive_slug)
    drive = get_object_or_404(Drive, slug=drive_slug)
    category = drive.category.name.lower()
    context = {}

    if category == 'onedrive':
        absolute_path = str(PurePath(drive.root, path).as_posix())
        cache_name = drive.slug+'-'+absolute_path
        if cache.get(cache_name):
            context = cache.get(cache_name)
        else:
            context = onedrive.get_context(drive, path, absolute_path)
            cache.set(cache_name, context)
    elif category == 'aliyun':
        context = aliyundrive.get_context(drive, path)
    elif category == 'local':
        root = Path(settings.LOCALE_STORAGE_PATH, drive.root)
        full_path = root / path

        if full_path.is_file():
            return download(request, full_path)
        context = local.get_context(drive, path)

    # redirect
    if not isinstance(context, dict):
        return context
    return render(request, 'storage/list.html', context)


def preview(request, path, drive_slug):
    drive = get_object_or_404(Drive, slug=drive_slug)
    full_path = str(PurePath(drive.root, path))
    category = drive.category.name.lower()
    name = prefix = ''
    if category == 'onedrive':
        result = onedrive.get_file(token=drive.access_token, path=full_path)
        name = result.get('name')
        prefix = file_type(name.split('.')[-1])
    elif category == 'aliyun':
        result = aliyundrive.get_download_url(access_token=drive.access_token, drive_id=drive.client_id, file_id=path)
        url = result.get('url')
        name = get_aliyundrive_filename(url)
        prefix = file_type(name.split('.')[-1])
    elif category == 'local':
        local_path = Path(settings.LOCALE_STORAGE_PATH, drive.root)
        file_path = local_path / path
        name = file_path.name
        prefix = file_type(file_path.suffix.replace('.', ''))
    context = {
        'breadcrumbs': generate_breadcrumbs(drive_slug, path),
        'name': name,
        'file_type': prefix
    }
    return render(request, 'storage/preview.html', context=context)


def download(request, path):
    # download local file
    file = open(path, 'rb')
    response = FileResponse(file)
    return response


@login_required
def delete(request):
    if request.method == 'POST':
        path = request.GET.get('path')
        if path:
            path = path.replace('%2F', '/')
        drive_slug = request.GET.get('drive')
        drive = get_object_or_404(Drive, slug=drive_slug)
        full_path = str(PurePath(drive.root, path))
        category = drive.category.name.lower()

        if category == 'onedrive':
            onedrive.delete_file(drive.access_token, path=full_path)
        elif category == 'aliyun':
            file_id = request.GET.get('fileId')
            aliyundrive.temporarily_delete_file(drive.access_token, drive.client_id, file_id)
        elif category == 'local':
            local.delete_file(full_path)
        return redirect(request.META.get('HTTP_REFERER'))


@login_required
def upload(request):
    pass


@login_required
def clear_cache(request, drive_slug, path):
    drive = get_object_or_404(Drive, slug=drive_slug)
    absolute_path = str(PurePath(drive.root, path).as_posix())
    cache_name = drive_slug+'-'+absolute_path
    if cache.get(cache_name):
        cache.delete(cache_name)
    return redirect(reverse('storage:list_files', args=(drive_slug, path)))
