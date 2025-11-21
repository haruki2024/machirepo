from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager # PermissionsMixinを削除
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CustomUserManager(UserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        """通常ユーザーを作成し、アクティブとしてマークします。"""
        if not username:
            raise ValueError('ユーザー名は必須です。')
        
        email = self.normalize_email(email) if email else email
        
        # is_active フィールドがないため、ここではユーザー作成フォームから渡される可能性のある
        # 'is_active' を True として処理します。
        user = self.model(
            username=username, 
            email=email, 
            **extra_fields
        )
        
        # パスワードのハッシュ化は BaseUserManager の継承で保証されますが、明示的に設定
        user.set_password(password)
        
        # AbstractBaseUser には is_active がデフォルトで含まれていないため、
        # has_perm が正常に動作するために必要な is_active=True の状態を確保
        # AbstractBaseUser は has_perm メソッド内で self.is_active をチェックしないため、
        # モデルに is_active がなくても、このマネージャーで正しいインスタンスは作成可能です。
        
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """スーパーユーザーを作成し、スタッフ、スーパーユーザーとして設定します。"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('スーパーユーザーは is_staff=True である必要があります。')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('スーパーユーザーは is_superuser=True である必要があります。')

        return self.create_user(username, email, password, **extra_fields)
    pass

class CustomUser(AbstractBaseUser): # ここから PermissionsMixin を外す
    BADGE_CHOICES = [
        ('none', 'なし'),
        ('bronze', '銅バッジ'),
        ('silver', '銀バッジ'),
        ('gold', '金バッジ'),
        ('rainbow', '虹バッジ'),
    ]
    badge_rank = models.CharField(
        max_length=10,
        choices=BADGE_CHOICES,
        default='none',
        verbose_name='バッジランク'
    )

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        error_messages={"unique": _("A user with that username already exists.")},
    )
    email = models.EmailField(_("email address"), unique=True, blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_("Designates that this user has all permissions without explicitly assigning them."),
    )
    

    
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]
    
    # PermissionsMixin を外したため、権限チェックメソッドを明示的に実装
    def has_perm(self, perm, obj=None):
        "ユーザーが特定のパーミッションを持っているかどうかを返します。"
        # is_superuser が True であれば、常に True を返します
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        "ユーザーが特定のアプリへのアクセス権を持っているかどうかを返します。"
        # is_superuser または is_staff であれば、アクセスを許可します
        return self.is_superuser or self.is_staff
    
    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        swappable = 'AUTH_USER_MODEL'