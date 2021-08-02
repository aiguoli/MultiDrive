from django.db import models
from django.utils import timezone


class Category(models.Model):
    """网盘分类"""
    name = models.CharField(verbose_name='分类名称', max_length=30)

    class Meta:
        ordering = ['name']
        verbose_name = "分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Drive(models.Model):
    """已挂载的网盘"""
    name = models.CharField('网盘名', max_length=30)
    slug = models.SlugField('展示名称', help_text='显示在url里面的字段', unique=True)
    root = models.CharField('展示目录', max_length=1024, help_text='格式：/home/share', default='/', null=True)
    client_id = models.TextField('client_id', null=True, blank=True)
    client_secret = models.TextField('client_secret', null=True, blank=True)
    access_token = models.TextField('access_token')
    refresh_token = models.TextField('get_refresh_token')
    category = models.ForeignKey(Category, verbose_name='分类', on_delete=models.CASCADE)
    created = models.DateTimeField('创建时间', default=timezone.now)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['created']
        verbose_name = "网盘"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class File(models.Model):
    name = models.CharField(verbose_name='文件名', max_length=256)
    file_id = models.CharField(verbose_name='文件ID', max_length=128, unique=True)
    size = models.IntegerField(verbose_name='文件大小', help_text='单位：B', blank=True, null=True)
    password = models.CharField(verbose_name='文件夹密码', max_length=256, blank=True)
    is_dir = models.BooleanField(verbose_name='是否是文件夹', default=False)
    parent_path = models.CharField(verbose_name='父目录', max_length=256)

    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    drive = models.ForeignKey('Drive', on_delete=models.CASCADE)

    created = models.DateTimeField('创建时间', default=timezone.now)
    updated = models.DateTimeField('更新时间', auto_now=True)

    def is_file(self):
        return not self.is_dir


class WebSettings(models.Model):
    """网站设置"""
    title = models.CharField(verbose_name='网站标题', max_length=30, blank=True)
    sub_title = models.CharField(verbose_name='副标题', max_length=120, blank=True)

    class Meta:
        verbose_name = "网站设置"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


