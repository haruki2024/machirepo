"""machirepo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
"""
# machirepo/urls.py

import os
from django.conf import settings
from django.contrib import admin 
from django.urls import path, include
from django.conf.urls.static import static # static関数をインポート
from django.contrib.auth import views as auth_views 
from main.forms import EmailAuthenticationForm 

urlpatterns = [
    # ここで admin が使用されています
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    
    # ログインビューのオーバーライド
    path('accounts/login/', 
         auth_views.LoginView.as_view(
             template_name='registration/login.html', 
             authentication_form=EmailAuthenticationForm
         ), 
         name='login'),
         
    # 標準認証URLをインクルード
    path('accounts/', include('django.contrib.auth.urls')), 
]

if settings.DEBUG:
    # MEDIA_URL (例: /media/) へのリクエストを MEDIA_ROOT (例: BASE_DIR/media/) から配信する設定
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # 開発時にSTATICファイルを確実に配信するための設定 (通常は自動で処理されますが念のため)
    # settings.STATIC_ROOT が settings.py に定義されているか確認してください
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
