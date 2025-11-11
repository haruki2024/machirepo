from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

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
    path('mypage/history/', views.post_history, name='post_history'),
    path('posts/', views.post_list, name='post_list'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),

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
    path('manage/users/', views.admin_user_list, name='admin_user_list'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete_confirm, name='admin_user_delete_confirm'),
    path('manage/users/delete/complete/', views.admin_user_delete_complete, name='admin_user_delete_complete'),
    path('manage/posts/', views.admin_post_list, name='admin_post_list'),
    path('manage/posts/<int:post_id>/detail/', views.admin_post_detail, name='admin_post_detail'), 
    path('manage/posts/<int:post_id>/status/edit/', views.manage_post_status_edit, name='admin_post_status_edit'),
    path('manage/posts/<int:post_id>/status/complete/', views.manage_status_edit_done, name='admin_status_edit_done'), 
    path('manage/posts/<int:post_id>/delete/', views.admin_post_delete, name='admin_post_delete'),
    path('manage/posts/delete/complete/', views.admin_post_delete_complete, name='admin_post_delete_complete'),

    # --------------------------------------------------
    # 3. 管理者向けタグ管理画面 (新規追加)
    # --------------------------------------------------
    path('manage/tags/', views.admin_tag_list, name='admin_tag_list'),
    path('manage/tags/add/', views.admin_tag_create, name='admin_tag_create'),
    path('manage/tags/<int:pk>/edit/', views.admin_tag_edit, name='admin_tag_edit'), 
    path('manage/tags/<int:pk>/delete/', views.admin_tag_delete, name='ademin_tag_delete'),
    path('manage/tags/create/complete/', views.admin_tag_create_complete, name='admin_tag_create_complete'),
    path('manage/tags/edit/complete/', views.admin_tag_edit_complete, name='admin_tag_edit_complete'),
    path('manage/tags/delete/complete/', views.admin_tag_delete_complete, name='admin_tag_delete_complete'),


]
