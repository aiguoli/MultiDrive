from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore
from .models import Drive
from .drives import onedrive, aliyundrive

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
scheduler.add_jobstore(DjangoJobStore(), "default")


def refresh_onedrive_token_by_id(drive_id):
    drive = Drive.objects.get(id=drive_id)
    if drive:
        tokens = onedrive.refresh_token(token=drive.refresh_token, client_id=drive.client_id,
                                        client_secret=drive.client_secret)
        drive.access_token = tokens.get('access_token')
        drive.refresh_token = tokens.get('refresh_token')
        drive.save()
        return 'Refresh token successfully'
    return 'Fail to find driver'


def refresh_aliyundrive_token_by_id(drive_id):
    drive = Drive.objects.get(id=drive_id)
    if drive:
        tokens = aliyundrive.refresh_token(refresh_token=drive.refresh_token)
        drive.access_token = tokens.get('access_token')
        drive.refresh_token = tokens.get('refresh_token')
        drive.save()
        return 'Refresh token successfully'
    return 'Fail to find driver'
