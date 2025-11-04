from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# アプリケーションの名前空間 (名前空間を付けずに直接参照できるように、この行は削除またはコメントアウトすべきですが、
# 今回は既存のコードの他の箇所への影響を最小限にするため、このままにしておき、
# テンプレート側で名前空間なしで動作させるために、一時的に名前空間参照なしで動作する可能性を許容します。
# ただし、最も安全な修正はテンプレート側で 'main:admin_post_list' にすることです。)

# 今回は NoReverseMatch が発生しているため、`app_name`を削除し、
# ルートの名前空間で解決できるようにします。
# app_name = 'main' # <- この行を削除/コメントアウトします。

urlpatterns = [
    # --------------------------------------------------
    # 1. 共通/認証関連
    # --------------------------------------------------
    path('', views.index, name='index'),
    path('redirect/', views.home_redirect, name='home_redirect'),
    path('signup/', views.ResidentRegisterView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.user_logout_view, name='logout'), # カスタムログアウトビューを使用

    # --------------------------------------------------
    # 2. ユーザー画面
    # --------------------------------------------------
    path('home/', views.user_home, name='user_home'),
    path('mypage/', views.my_page, name='my_page'),
    path('posts/', views.post_list, name='post_list'),
    
    # --------------------------------------------------
    # 3. 投稿フロー
    # --------------------------------------------------
    path('post/create/', views.photo_post_create, name='photo_post_create'),
    path('post/location/', views.photo_post_manual_location, name='photo_post_location'),
    path('post/confirm/', views.photo_post_confirm, name='photo_post_confirm'),
    path('post/done/', views.photo_post_done, name='photo_post_done'),


    # --------------------------------------------------
    # 4. 管理者画面 (manage/ に統一)
    # --------------------------------------------------
    path('manage/home/', views.admin_home, name='admin_home'),
    
    # ユーザー管理
    path('manage/users/', views.admin_user_list, name='admin_user_list'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete_confirm, name='admin_user_delete_confirm'),
    path('manage/users/delete/complete/', views.admin_user_delete_complete, name='admin_user_delete_complete'),

    # 報告管理 (一覧・詳細・ステータス編集)
    path('manage/posts/', views.admin_post_list, name='admin_post_list'),
    # /detail/ を含むパスに対応 (例: manage/posts/13/detail/ に対応)
    path('manage/posts/<int:post_id>/detail/', views.admin_post_detail, name='admin_post_detail'), 
    path('manage/posts/<int:post_id>/status_edit/', views.admin_post_status_edit, name='admin_post_status_edit'),
    path('manage/posts/<int:post_id>/status_edit/done/', views.admin_status_edit_done, name='admin_status_edit_done'),
    
    # 報告削除処理 
    path('manage/posts/<int:post_id>/delete/', views.admin_post_delete, name='admin_post_delete'),
    path('manage/posts/delete/complete/', views.admin_post_delete_complete, name='admin_post_delete_complete'),

]
