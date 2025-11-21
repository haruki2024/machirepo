import logging
import os 
import decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView
from django.contrib.auth import get_user_model, logout,login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.exceptions import ValidationError 
from django.core.files.base import ContentFile
from .forms import ManualLocationForm
from django.core.files.storage import FileSystemStorage 
from . import models 
from .models import PhotoPost, Tag
from .forms import TagForm, StatusUpdateForm, ResidentCreationForm, PhotoPostForm, ManualLocationForm, UserUpdateForm
from django.views.generic.edit import UpdateView 

logger = logging.getLogger(__name__)
fs = FileSystemStorage()

# -----------------------------------------------------
# 権限チェック
# -----------------------------------------------------
def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# -----------------------------------------------------
# 1. 共通/認証関連ビュー
# -----------------------------------------------------

def index(request):
    if request.user.is_authenticated:
        return redirect('home_redirect')
    
    return render(request, 'index.html')

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('admin_home')
    else:
        return redirect('user_home')

class ResidentRegisterView(CreateView):
    
    form_class = ResidentCreationForm
    model = get_user_model()
    success_url = reverse_lazy('home_redirect')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # ユーザーインスタンスをセッションに保存（ログイン処理）
        login(self.request, self.object) 
        
        messages.success(self.request, "アカウントが作成され、ログインしました！")
        
        return response


    def form_invalid(self, form):
        logger.error("--- ResidentCreationForm バリデーション失敗エラー詳細 ---")
        for field, errors in form.errors.items():
            logger.error(f"フィールド '{field}': {errors}")
        logger.error("---------------------------------------------------------------")
        return super().form_invalid(form)
    
def user_logout_view(request):
    """ユーザーログアウト (urls.pyの'logout/'に対応)"""
    logout(request)
    messages.success(request, "ログアウトしました。")
    return redirect('index')

# -----------------------------------------------------
# 2. ユーザー画面ビュー
# -----------------------------------------------------
@login_required
def user_home(request):
    latest_posts = models.PhotoPost.objects.order_by('-posted_at')[:2]
    
    context = {'latest_posts': latest_posts} 
    
    return render(request, 'main/user/user_home.html', context)


def user_terms(request):
    latest_posts = models.PhotoPost.objects.order_by('-posted_at')[:2]
    
    context = {'latest_posts': latest_posts} 
    
    
    return render(request, 'main/user/user_terms.html', context)

@login_required
def user_about(request):
    latest_posts = models.PhotoPost.objects.order_by('-posted_at')[:2]
    



    context = {'latest_posts': latest_posts} 
    



    return render(request, 'main/user/user_about.html', context)


@login_required
def user_stamp(request):
    post_count = 0
    card = 0
    
    posts = PhotoPost.objects.filter(user=request.user).order_by('-posted_at') 
    for i in posts:
        post_count += 1
    card = post_count / 10
    if post_count > 10:
        post_count -= (int(card)*10)

    context = {
                'stamp': range(post_count),
                'notstamp':range(10-post_count),
                'card':int(card),
                }

    print(post_count)
    return render(request, 'main/user/user_stamp.html', context)






@login_required
def my_page(request):
    posts = models.PhotoPost.objects.filter(user=request.user).order_by('-posted_at')
    
    post_count = 0
    card = 0
    
    for i in posts:
        post_count += 1
    
    card = int(post_count / 10)
    
    if post_count > 10:
        post_count -= (card*10)
    
    context = {
                'user': request.user,
                'posts': posts,
                'card':int(card),
                }
    
    return render(request, 'main/user/user_mypage.html', context)





@login_required
def post_history(request):
    posts = PhotoPost.objects.filter(user=request.user).order_by('-posted_at') 

    STATUS_CHOICES_DISPLAY = dict(PhotoPost.STATUS_CHOICES) 
    PRIORITY_CHOICES_DISPLAY = dict(PhotoPost.PRIORITY_CHOICES) 

    context = {
        'posts': posts,
        'STATUS_CHOICES_DISPLAY': STATUS_CHOICES_DISPLAY,
        'PRIORITY_CHOICES_DISPLAY': PRIORITY_CHOICES_DISPLAY,
    }
    return render(request, 'main/user/user_post_history.html', context)


def post_list(request):
    status_filter = request.GET.get('status')
    tag_filter = request.GET.get('tag')

    posts = models.PhotoPost.objects.select_related('user', 'tag').order_by('-posted_at')

    valid_statuses = [key for key, _ in models.PhotoPost.STATUS_CHOICES]
    if status_filter in valid_statuses:
        posts = posts.filter(status=status_filter)

    if tag_filter:
        try:
            tag_id = int(tag_filter)
            posts = posts.filter(tag__id=tag_id)
        except ValueError:
            logger.warning(f"無効なタグID: {tag_filter}")



    context = {
        'posts': posts,
        'status_filter': status_filter,
        'tag_filter': tag_filter,
        'all_tags': models.Tag.objects.order_by('name'),
        'status_choices': models.PhotoPost.STATUS_CHOICES,
        'priority_choices': models.PhotoPost.PRIORITY_CHOICES,
    }

    return render(request, 'main/user/user_post_list.html', context)

@method_decorator(login_required, name='dispatch')
class UserProfileUpdateView(UpdateView):
    """ユーザー情報編集"""
    model = get_user_model()
    form_class = UserUpdateForm 
    template_name = 'main/user/user_profile_edit.html'

    def get_success_url(self):
        return reverse('user_edit_complete')

    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        if not form.cleaned_data.get('badge_rank'):
            form.instance.badge_rank = 'none'
        return super().form_valid(form)



    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
       

        post_count = 0
        card = 0
        posts = PhotoPost.objects.filter(user=user).order_by('-posted_at')
        for i in posts:
            post_count += 1
        card = post_count / 10


        badge_choices = []
        if post_count > 10:
            post_count -= (int(card)*10)
            badge_choices = []
        if card >= 1:
            badge_choices.append(('bronze', '銅バッジ'))
        if card >= 2:
            badge_choices.append(('silver', '銀バッジ'))
        if card >= 3:
            badge_choices.append(('gold', '金バッジ'))
        if card >= 5:
            badge_choices.append(('rainbow', '虹バッジ'))

        if not badge_choices:
            badge_choices = [('none', '表示しない')]

        # フォームに渡す
        kwargs['badge_choices'] = badge_choices
        return kwargs

    def form_valid(self, form):
        # 選択肢が 'none' しかない場合は強制的に none をセット
        choices = dict(form.fields['badge_rank'].choices)
        if list(choices.keys()) == ['none']:
            form.instance.badge_rank = 'none'

        return super().form_valid(form)




user_profile_edit = UserProfileUpdateView.as_view()

@login_required
def user_edit_complete(request):
    """アカウント情報編集完了画面"""
    return render(request, 'main/user/user_edit_complete.html', {})




# -----------------------------------------------------
# 3. 投稿フロービュー
# -----------------------------------------------------
@login_required
def photo_post_create(request):
    post_data = request.session.get('post_data', {})
    
    if request.method == 'GET':
        keys_to_remove = ['latitude', 'longitude', 'title', 'tag_pk', 'comment', 'photo_path'] 
        
        if any(k in post_data for k in keys_to_remove):
            if 'photo_path' in post_data and post_data['photo_path']:
                try:
                    fs.delete(post_data['photo_path'])
                    logger.info(f"--- TEMP FILE CLEANUP: {post_data['photo_path']} deleted on Step 1 GET. ---")
                except Exception:
                    logger.warning("Failed to delete old session photo file.")
            
            post_data = {k: v for k, v in post_data.items() if k not in keys_to_remove}
            request.session['post_data'] = post_data
            logger.info("--- SESSION CLEANUP: Old form data cleared from post_data. ---")

        if 'post_photo_data' in request.session:
            del request.session['post_photo_data']
            logger.info("--- SESSION CLEANUP: 'post_photo_data' cleared. ---")


    if request.method == 'POST':
        print("--- DEBUG: POST Request received on Step 1 (photo_post_create) ---")
        
        form = PhotoPostForm(request.POST, request.FILES, initial=post_data)
        
        if form.is_valid():
            cleaned_tag = form.cleaned_data['tag'] 
            tag_pk_to_save = cleaned_tag.pk if cleaned_tag else None    
            current_photo_path = post_data.get('photo_path')
        
            new_post_data = {
                'title': form.cleaned_data['title'],
                'comment': form.cleaned_data['comment'],
                'tag_pk': tag_pk_to_save,
                'latitude': request.POST.get('latitude', '0.0'),   
                'longitude': request.POST.get('longitude', '0.0'),
			}
            
            if current_photo_path and 'photo' not in request.FILES:
                new_post_data['photo_path'] = current_photo_path
            
            photo_file = request.FILES.get('photo')
            if photo_file:
                
                if 'photo_path' in post_data and post_data['photo_path']:
                    try:
                        # ファイルパスがセッションに保存されていると仮定し、削除
                        fs.delete(post_data['photo_path'])
                        logger.info(f"--- OLD TEMP FILE DELETED: {post_data['photo_path']} ---")
                    except Exception:
                        logger.warning("Failed to delete old session photo file.")
                
                filename = fs.save(photo_file.name, photo_file)
                new_post_data['photo_path'] = filename
                
            request.session['post_data'] = new_post_data

            logger.info("--- SESSION SAVE: Form data and photo path saved to session. ---")
            
            return redirect('photo_post_location')
        
        else:
            logger.error("PhotoPostForm validation failed: %s", form.errors)
            messages.error(request, "投稿内容にエラーがあります。不足している必須項目（写真、カテゴリ、タイトル）を確認するか、写真のファイルサイズ（最大5MB）を確認してください。")
    
    else:
        initial_data = post_data.copy()
        
        tag_pk = initial_data.get('tag_pk')
        if tag_pk:
            try:
                initial_data['tag'] = models.Tag.objects.get(pk=tag_pk) 
            except (models.Tag.DoesNotExist, ValueError):
                initial_data['tag'] = None
                
        form = PhotoPostForm(initial=initial_data)
    
    return render(request, 'main/user/user_photo_post_create.html', {'form': form, 'step': 1})


@login_required
def photo_post_manual_location(request):
    post_data = request.session.get('post_data')
    
    if not post_data:
        messages.error(request, "報告のデータが見つかりませんでした。最初からやり直してください。")
        return redirect('photo_post_create')
        
    def is_valid_coord(val):
        try:
            f_val = float(val)
            return abs(f_val) > 0.000001
        except (ValueError, TypeError):
            return False

    session_lat = post_data.get('latitude')
    session_lng = post_data.get('longitude')
    
    if is_valid_coord(session_lat) and is_valid_coord(session_lng):
        return redirect('photo_post_confirm')
    

    if request.method == 'POST':
        posted_lat = request.POST.get('latitude')
        posted_lng = request.POST.get('longitude')

        try:
            lat = float(posted_lat)
            lng = float(posted_lng)

            post_data['latitude'] = lat
            post_data['longitude'] = lng
            
            request.session['post_data'] = post_data
            
            return redirect('photo_post_confirm')
        
        except (TypeError, ValueError):
            messages.error(request, "位置情報の値が不正です。再度地図で場所を選択してください。") 
          
    form = ManualLocationForm(initial=post_data) 
    
    context = {
        'manual_form': form, 
        'post_data': post_data,
        'step': 2
    }
    return render(request, 'main/user/user_photo_post_manual_location.html', context)


@login_required
def photo_post_confirm(request):
    post_data = request.session.get('post_data')
    
    if not post_data or 'photo_path' not in post_data:
        messages.error(request, "データが不足しています。写真と必須項目を確認し、最初からやり直してください。")
        return redirect('photo_post_create')
        
    def safe_float(value):
        
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return None
        
        try:
            value_as_str = str(value) 
            decimal_val = decimal.Decimal(value_as_str)     
            rounded_val = decimal_val.quantize(decimal.Decimal('0.0000000000001'), rounding=decimal.ROUND_HALF_UP)
            
            return rounded_val
            
        except (decimal.InvalidOperation, TypeError, ValueError):
            logger.error(f"Failed to convert or quantize coordinate value: {value}")
            return None

    latitude_val = None
    longitude_val = None

    if request.method == 'POST':
        photo_path = post_data.get('photo_path')
        
        try:
            latitude_val = safe_float(post_data.get('latitude'))
            longitude_val = safe_float(post_data.get('longitude'))
            new_post = models.PhotoPost(
                user=request.user,
                title=post_data.get('title'), 
                comment=post_data.get('comment'),
                latitude=latitude_val, 
                longitude=longitude_val,
            )

            tag_pk = post_data.get('tag_pk') 
            if tag_pk:
                try:
                    tag_instance = models.Tag.objects.get(pk=tag_pk)
                    new_post.tag = tag_instance
                except models.Tag.DoesNotExist:
                    logger.warning(f"投稿保存時にタグID {tag_pk} が見つかりませんでした。タグなしで保存されます。")
                    new_post.tag = None
            else:
                new_post.tag = None
            
            if photo_path and fs.exists(fs.path(photo_path)):
                with fs.open(photo_path, 'rb') as f:
                    file_name = os.path.basename(photo_path)
                    new_post.photo.save(file_name, ContentFile(f.read()), save=False)
                logger.info(f"--- PHOTO LOAD SUCCESS: Temporary photo loaded from disk at {photo_path} ---")
            else:
                logger.error(f"FATAL: Temporary photo file not found at path: {photo_path}")
                raise ValidationError({'photo': '一時的な写真ファイルが見つからないか、有効期限切れです。'})
            


            if tag_pk:
                print(f"--- DEBUG SAVE: Tag PK={tag_pk} found. Tag instance ID to save: {new_post.tag.pk}")
            else:
                print("--- DEBUG SAVE: Tag is None. ---")
           
            new_post.full_clean()
            new_post.save()

            del request.session['post_data']
            if photo_path and fs.exists(fs.path(photo_path)):
                fs.delete(photo_path)
                logger.info(f"--- TEMP FILE DELETED: {photo_path} ---")
            
            return redirect('photo_post_done')
            
        except ValidationError as e:
            # データ検証エラー：緯度経度や必須項目などのエラー
            error_messages = "\n".join([f"「{k}」: {v[0]}" for k, v in e.message_dict.items()])
            logger.error("投稿のfull_clean()が失敗しました: %s", error_messages)
            messages.error(request, f"**データ検証エラー**：投稿の保存に必要な情報が不足しています。不足フィールド:\n{error_messages}")
            
            return redirect('photo_post_create')
            
        except Exception as e:
            logger.error("--- FATAL ERROR: 報告保存時の予期せぬエラーが発生 ---", exc_info=True)
            messages.error(request, f"**投稿通信エラー**：報告の保存中に予期せぬエラーが発生しました。再度投稿してください。エラー: {e}")
            return redirect('photo_post_create')
            
    tag_pk = post_data.get('tag_pk')
    selected_tag = None
    if tag_pk:
        try:
            selected_tag = models.Tag.objects.get(pk=tag_pk)
        except models.Tag.DoesNotExist:
            logger.error(f"確認画面でタグID {tag_pk} が見つかりません。")
            pass
            
    context = {
        'post_data': post_data,
        'selected_tag': selected_tag, 
        'step': 3
    }
    return render(request, 'main/user/user_photo_post_confirm.html', context)

@login_required
def photo_post_done(request):
    return render(request, 'main/user/user_photo_post_complete.html', {})


def post_detail(request, post_id):
    post = get_object_or_404(
        models.PhotoPost.objects, 
        pk=post_id
    )
    
    selected_tag = post.tag
    context = {
        'post': post,
        'selected_tag': selected_tag,
    }
    return render(request, 'main/user/user_post_detail.html', context)


# -----------------------------------------------------
# 4. 管理者画面ビュー（スタッフ権限限定）
# -----------------------------------------------------

@user_passes_test(is_staff_user, login_url='/')
def admin_home(request):
    total_posts = models.PhotoPost.objects.count()
    new_posts_count = models.PhotoPost.objects.filter(status='new').count()
    
    context = {
        'total_posts': total_posts,
        'new_posts_count': new_posts_count
    }
    return render(request, 'main/admin/admin_home.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_user_list(request):
    User = get_user_model()
    users = User.objects.exclude(pk=request.user.pk).order_by('-date_joined')
    
    context = {
        'users': users,
        'app_name': 'ユーザー一覧'
    }
    return render(request, 'main/admin/admin_user_list.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_user_delete_confirm(request, user_id):
    User = get_user_model()

    if request.method == 'GET':
        return redirect('admin_user_list')
    
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, pk=user_id)
        
        if user_to_delete.pk == request.user.pk:
            messages.error(request, "自分自身のアカウントをこの画面から削除することはできません。")
            return redirect('admin_user_list')
        
        try:
            username = user_to_delete.username
            user_to_delete.delete()
            
            messages.success(request, f"ユーザー「{username}」を削除しました。")
            
            return redirect('admin_user_delete_complete')
            
        except Exception as e:
            logger.error(f"ユーザーID {user_id} の削除中にエラーが発生: {e}", exc_info=True)
            messages.error(request, f"削除中に予期せぬエラーが発生しました。詳細: {e}")
            return redirect('admin_user_list')

@user_passes_test(is_staff_user, login_url='/')
def admin_user_delete_complete(request):
    context = {
        'app_name': '削除完了'
    }
    return render(request, 'main/admin/admin_user_delete_complete.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_post_list(request):

    status_filter = request.GET.get('status', None)
    tag_filter = request.GET.get('tag', None)
    priority_filter = request.GET.get('priority', None)

    posts = models.PhotoPost.objects.all().select_related('user').select_related('tag').order_by('-posted_at')
  
    valid_statuses = dict(models.PhotoPost.STATUS_CHOICES).keys()
    if status_filter in valid_statuses:
        posts = posts.filter(status=status_filter)

    if tag_filter:
        try:
            tag_id = int(tag_filter)
            posts = posts.filter(tag__id=tag_id)
        except ValueError:
            
            pass

    if priority_filter:
        if priority_filter == '__none__':
            posts = posts.filter(priority__isnull=True)
        else:
            posts = posts.filter(priority=priority_filter)

    all_tags = models.Tag.objects.all().order_by('name')

    context = {
        'posts': posts,
        'status_filter': status_filter,
        'tag_filter': tag_filter,
        'priority_filter': priority_filter,
        'all_tags': all_tags,
    }
    return render(request, 'main/admin/admin_post_list.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_post_detail(request, post_id):
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    form = StatusUpdateForm(instance=post)
    context = {
        'post': post,
        'form': form
    }
    return render(request, 'main/admin/admin_post_detail.html', context)


@user_passes_test(is_staff_user, login_url='/')
def manage_post_status_edit(request, post_id):
    """ステータス編集画面"""
    post = get_object_or_404(models.PhotoPost, pk=post_id)

    if request.method == 'POST':
        form = StatusUpdateForm(request.POST, instance=post) 
        if form.is_valid():
            updated_post = form.save() 
            messages.success(request, f"報告 (ID: {post_id}) のステータスと優先順位を更新しました。")
            
            return redirect('admin_status_edit_done', post_id=updated_post.pk) 
    else:
        form = StatusUpdateForm(instance=post)

    context = {
        'form': form,
        'post': post
    }
    return render(request, 'main/admin/admin_post_status_edit.html', context)


@user_passes_test(is_staff_user, login_url='/')
def manage_status_edit_done(request, post_id): 
    """ステータス編集完了画面"""
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    context = {'post': post}
    return render(request, 'main/admin/admin_post_status_complete.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_post_delete(request, post_id):
    """報告の削除処理"""
    post = get_object_or_404(models.PhotoPost, pk=post_id)

    if request.method == 'POST':
        post_pk = post.pk
        post_title = (post.comment[:20] + '...') if post.comment and len(post.comment) > 20 else post.comment or f"ID:{post_pk}の報告"

        try:
            post.delete()

            messages.success(request, f"報告「{post_title}」を削除しました。")

            return redirect('admin_post_delete_complete')

        except Exception as e:
            logger.error(f"報告ID {post_id} の削除中にエラーが発生: {e}", exc_info=True)
            messages.error(request, "報告の削除中に予期せぬエラーが発生しました。")
            return redirect('admin_post_detail', post_id=post_id)

    messages.error(request, "報告の削除にはPOSTリクエストが必要です。")
    return redirect('admin_post_detail', post_id=post_id)

@user_passes_test(is_staff_user, login_url='/')
def admin_post_delete_complete(request):
    """報告削除完了画面"""
    context = {
        'app_name': '報告削除完了'
    }
    return render(request, 'main/admin/admin_post_delete_complete.html', context)

# --------------------------------------------------
# 5. 管理者向けタグ管理画面 (新規追加)
# --------------------------------------------------
@login_required
def admin_tag_list(request):
    """タグ一覧表示画面"""
    tags = Tag.objects.all().order_by('name')
    context = {'tags': tags}
    return render(request, 'main/admin/admin_tag_list.html', context)

@login_required
def admin_tag_create(request):
    """タグ作成画面"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            return redirect('admin_tag_create_complete')
    else:
        form = TagForm()

    context = {
                'form': form,
                'page_title': '新規タグ追加'
                }
    return render(request, 'main/admin/admin_tag_create.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_tag_edit(request, pk):
    """タグ編集ビュー"""
    tag = get_object_or_404(Tag, pk=pk)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            updated_tag = form.save()
            return redirect('admin_tag_edit_complete')
    else:
        form = TagForm(instance=tag)
        
    context = {'form': form, 'tag': tag, 'page_title': 'タグ編集'}
    return render(request, 'main/admin/admin_tag_edit.html', context)

@login_required
def admin_tag_delete(request, pk):
    """タグ削除処理"""
    tag = get_object_or_404(Tag, pk=pk)
    
    if request.method == 'POST':
        tag_name = tag.name
        tag.delete()
        return redirect('admin_tag_delete_complete')
    
    return redirect('admin_tag_list') 


@login_required
def admin_tag_create_complete(request):
    """タグの追加 完了画面"""
    return render(request, 'main/admin/admin_tag_create_complete.html', {'page_title': '完了'})

@user_passes_test(is_staff_user, login_url='/')
def admin_tag_edit_complete(request):
    """タグの編集 完了画面"""
    return render(request, 'main/admin/admin_tag_edit_complete.html', {'page_title': '編集完了'})

@login_required
def admin_tag_delete_complete(request):
    """タグの削除 完了画面"""
    return render(request, 'main/admin/admin_tag_delete_complete.html', {'page_title': '完了'})

