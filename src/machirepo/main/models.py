from django.db import models
from django.utils import timezone
import uuid 
from django.conf import settings


# 投稿のカテゴリー分けに使用するタグモデル
class Tag(models.Model):
    """写真投稿のカテゴリ（タグ）を定義するモデル。"""
    name = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="タグ名"
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "タグ"
        verbose_name_plural = "タグ"


# 写真投稿モデル
class PhotoPost(models.Model):
    # -----------------------------------------------------
    # 管理者機能で使用するフィールド
    # -----------------------------------------------------
    STATUS_CHOICES = [
        ('new', '新規'),
        ('in_progress', '対応中'),
        ('completed', '対応完了'),
        ('not_required', '対応不可'),
    ]
    
    PRIORITY_CHOICES = [
        ('none', '--'),
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='対応状況'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='none',
        verbose_name='対応優先順位'
    )
    admin_note = models.TextField(
        verbose_name='管理者メモ/対応内容',
        blank=True,
        null=True,
    )
    
    # -----------------------------------------------------
    # 報告投稿時に必要なフィールド (ユーザー提供のコードに基づく)
    # -----------------------------------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="投稿ユーザー"
    )
    
    title = models.CharField(
        max_length=100, 
        verbose_name="タイトル",
        blank=True
    )
    
    comment = models.TextField(
        blank=True, 
        verbose_name="詳細コメント"
    )
    
    photo = models.ImageField(
        upload_to='photos/%Y/%m/%d/', 
        verbose_name="写真"
    )
    
    tag = models.ForeignKey(
        Tag, 
        on_delete=models.SET_NULL, 
        null=True,                 
        blank=True,                
        related_name='photo_posts', 
        verbose_name="メインカテゴリ"
    )
    
    latitude = models.DecimalField(
        max_digits=30,
        decimal_places=25,
        null=True,        
        blank=True,       
        verbose_name="緯度"
    )

    
    longitude = models.DecimalField(
        max_digits=30,
        decimal_places=25,
        null=True,
        blank=True,
        verbose_name="経度"
    )
    
    
    posted_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="投稿日時"
    )
    
    def __str__(self):
        return f"{self.title or 'タイトルなし'} by {self.user.username} ({self.posted_at.strftime('%Y-%m-%d')})"
    
    class Meta:
        verbose_name = "写真投稿"
        verbose_name_plural = "写真投稿"
        ordering = ['-posted_at']