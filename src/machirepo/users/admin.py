# users/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
# 💡 BaseUserAdminの代わりにUserAdminをインポート
from django.contrib.auth.admin import UserAdmin 
# 💡 (または 'django.contrib.auth.admin' に BaseUserAdmin がないことを確認)

CustomUser = get_user_model()

# UserAdmin を継承し、M2Mフィールドの表示を無効化
class CustomUserAdmin(UserAdmin):

    # ユーザー追加フォームは標準の UserCreationForm をそのまま使用
    # add_form = CustomUserCreationForm # ← もし独自のフォームがある場合はここに指定

    # ユーザー詳細画面に表示するフィールドの設定
    fieldsets = (
        (None, {'fields': ('username', 'password')}), # 認証情報
        (('Personal info'), {'fields': ('email',)}),  # 個人情報
        (('Permissions'), {
            # is_active フィールドがないため、is_staff と is_superuser のみ表示
            # モデルに is_active があればここに追加してください
            'fields': ('is_staff', 'is_superuser'), 
        }),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}), # 日付情報
    )

    # リスト表示に M2M 関連フィールドを含まない
    list_display = ('username', 'email', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    
    # 💡 M2M フィールドの設定を無効化するために、これらを空またはNoneに設定
    filter_horizontal = () 
    # M2M フィールドがないため、UserAdminの標準設定(groupsとuser_permissions)を上書きして削除
    # fieldsets からグループやパーミッションの設定も削除する必要があります。
    
    # UserAdminには add_fieldsets も含まれますが、ここでは省略して標準動作に任せます。

    ordering = ('username',)
    search_fields = ('username', 'email')


# カスタムUserモデルを管理画面に登録
admin.site.register(CustomUser, CustomUserAdmin)