from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CustomUserManager(UserManager):
    pass

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # AbstractUserの主要なフィールドを再定義 (first_name, last_nameは省略)
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
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Designates whether this user should be treated as active. Unselect this instead of deleting accounts."),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    # first_nameとlast_nameは意図的に定義しません。

    objects = CustomUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]
    
    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        # first_name/last_nameがないため、usernameをフルネームとして返します
        return self.username

    def get_short_name(self):
        return self.username

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        # 既存のUserモデルを置き換えるための必須設定
        swappable = 'AUTH_USER_MODEL'