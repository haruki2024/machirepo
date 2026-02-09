import os
from django.conf import settings
from django.contrib import admin 
from django.urls import path, include
from django.conf.urls.static import static # static関数をインポート
from django.contrib.auth import views as auth_views 
from main.forms import EmailAuthenticationForm 
from django.urls import path, re_path
from main import views as main_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=EmailAuthenticationForm), name='login'),
    path('main/', include('main.urls')), 
    path('accounts/', include('django.contrib.auth.urls')), 
    
    re_path(r'^(?!static/|media/).*$', main_views.custom_404_view, {'exception': Exception('Page not Found')}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
