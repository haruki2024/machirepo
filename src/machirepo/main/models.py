from django.db import models
from django.contrib.auth.models import User # ユーザー提供のコードに基づく
from django.utils import timezone
import uuid # UUIDフィールドは使用しないが、念のためimportは残しておく
# from taggit.managers import TaggableManager # TaggableManagerは使用しない


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
        default='medium',
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
    # IDフィールドは暗黙的に作成されるため、ここでは定義しない

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="投稿ユーザー"
    )
    
    # ★修正点: titleを非必須にする (null=True, blank=Trueを設定)★
    title = models.CharField(
        max_length=100, 
        verbose_name="タイトル",
        blank=True # フォームで空入力を許可（Step 1通過のため）
    )
    
    
    comment = models.TextField(
        blank=True, 
        verbose_name="詳細コメント"
    )
    
    photo = models.ImageField(
        upload_to='photos/%Y/%m/%d/', 
        verbose_name="写真"
    )
    
    # 投稿が関連付けられているタグ（多対多の関係）
    tags = models.ManyToManyField(
        Tag, 
        related_name='photo_posts', 
        verbose_name="カテゴリ"
    )
    
    # 地理情報
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        verbose_name='緯度', 
        null=True, 
        blank=True 
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        verbose_name='経度', 
        null=True, 
        blank=True 
    )
    
    # 地名（手動入力または取得した地名）
    location_name = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="地名"
    )
    
    posted_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="投稿日時"
    )
    
    def __str__(self):
        # ユーザー提供の__str__メソッドを尊重
        return f"{self.title or 'タイトルなし'} by {self.user.username} ({self.posted_at.strftime('%Y-%m-%d')})"
    
    class Meta:
        verbose_name = "写真投稿"
        verbose_name_plural = "写真投稿"
        ordering = ['-posted_at']