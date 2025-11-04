from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.exceptions import ValidationError 
import logging
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile 
from django.db.models import Q 

# ロガーの設定
logger = logging.getLogger(__name__)

# モデルとフォームのインポート
from . import models 
from .forms import StatusUpdateForm, ResidentCreationForm, PhotoPostForm, ManualLocationForm 

# -----------------------------------------------------
# 権限チェックヘルパー
# -----------------------------------------------------
def is_staff_user(user):
    """Staff権限チェック用ヘルパー関数"""
    return user.is_authenticated and user.is_staff

# -----------------------------------------------------
# 1. 共通/認証関連ビュー
# -----------------------------------------------------

def index(request):
    """
    トップページ。認証済みユーザーはホームにリダイレクト。未認証はログイン画面などへ。
    """
    if request.user.is_authenticated:
        return redirect('home_redirect')
    
    return render(request, 'index.html')

def home_redirect(request):
    """認証後のリダイレクト先。権限によって画面を振り分ける。"""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_staff:
        return redirect('admin_home')
    else:
        return redirect('user_home')

class ResidentRegisterView(CreateView):
    """新規ユーザー登録ビュー"""
    form_class = ResidentCreationForm
    model = get_user_model()
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    
    # 💡 【デバッグ追加】フォームバリデーション失敗時にエラー内容をログに出力
    def form_invalid(self, form):
        logger.error("--- 🚨 ResidentCreationForm バリデーション失敗エラー詳細 🚨 ---")
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
    posts = models.PhotoPost.objects.exclude(status='not_required').order_by('-posted_at')[:5]
    context = {'posts': posts}
    # ① 住民は住民用トップ画面から「新規投稿を行う」を押す (リンクとして配置されることを想定)
    return render(request, 'main/user_home.html', context)

@login_required
def my_page(request):
    my_posts = models.PhotoPost.objects.filter(user=request.user).order_by('-posted_at')
    context = {'my_posts': my_posts}
    return render(request, 'main/my_page.html', context)

def post_list(request):
    posts = models.PhotoPost.objects.exclude(status='not_required').order_by('-posted_at')
    context = {'posts': posts}
    return render(request, 'main/post_list.html', context)


# -----------------------------------------------------
# 3. 投稿フロービュー
# -----------------------------------------------------
@login_required
def photo_post_create(request):
    """基本フロー②/③/④ - 報告作成ステップ1: 写真/コメント入力"""
    post_data = request.session.get('post_data', {})
    
    # 【ステップ1クリーンアップ】
    if request.method == 'GET':
        # ★修正: titleとtagsをセッションクリア対象に追加★ (元々あったロジックを保持)
        keys_to_remove = ['latitude', 'longitude', 'title', 'tags', 'comment'] # commentも追加
        if any(k in post_data for k in keys_to_remove):
            # post_dataから指定キーを除外してセッションに再保存
            post_data = {k: v for k, v in post_data.items() if k not in keys_to_remove}
            request.session['post_data'] = post_data
            logger.info("--- SESSION CLEANUP: Old location, title, tags, and comment data cleared from session on Step 1 GET. ---")

    if request.method == 'POST':
        # --- POSTリクエストを受信したことを確認 ---
        print("--- DEBUG: POST Request received on Step 1 (photo_post_create) ---")
        
        # GETリクエストでセッションに保持していたデータを使って初期化
        form = PhotoPostForm(request.POST, request.FILES, initial=post_data)
        
        if form.is_valid():
            # =================================================================
            # ★★★ 修正箇所: tagsのセッション保存方法を単一PKに変更 ★★★
            # =================================================================
            
            # 1. フォームデータをセッションに保存
            
            # tagsを処理: 単一のTagオブジェクトの場合はそのPKを保存
            cleaned_tag = form.cleaned_data['tags']
            tag_pk_to_save = cleaned_tag.pk if cleaned_tag else None
            
            request.session['post_data'] = {
                'title': form.cleaned_data['title'],
                'comment': form.cleaned_data['comment'],
                'tags': tag_pk_to_save, # ここが修正されました
                'latitude': '0.0', # 仮の値。次のステップで上書きされる
                'longitude': '0.0', # 仮の値。次のステップで上書きされる
            }

            # 2. 画像ファイルをセッションに保存 (前回のロジックを保持)
            photo_file = request.FILES.get('photo')
            if photo_file:
                # ファイルストレージのインポートと処理
                from django.core.files.storage import FileSystemStorage
                fs = FileSystemStorage()
                
                # 既存のファイルがあれば削除
                if 'photo_path' in post_data and post_data['photo_path']:
                    # ファイルURLからファイル名を取得し削除 (環境依存の処理なので慎重に)
                    try:
                        # fs.delete()はファイル名/パスを期待するため、URLを元に戻す処理が必要な場合があります。
                        # ここでは簡単のため、ファイルパスがセッションに保存されていると仮定します。
                        if post_data['photo_path'].startswith(fs.base_url):
                             old_filename = post_data['photo_path'].replace(fs.base_url, '', 1)
                             fs.delete(old_filename)
                        else:
                            # base_urlがない場合、ファイルパス自体が相対パスだと仮定
                            fs.delete(post_data['photo_path'])
                    except Exception:
                        logger.warning("Failed to delete old session photo file: %s", post_data.get('photo_path'))
                
                # 新しいファイルを保存
                filename = fs.save(photo_file.name, photo_file)
                # セッションには相対パス(filename)を保存
                request.session['post_data']['photo_path'] = filename
                
            
            logger.info("--- SESSION SAVE: Form data and photo path saved to session. ---")
            
            # =================================================================
            # リダイレクトは 'photo_post_location' のままで続行
            # =================================================================
            
            # 基本フロー⑤の起点へ: 位置情報取得の起点となるステップ2へリダイレクト
            return redirect('photo_post_location')
        
        else:
            # === DEBUG/代替フロー①：必須項目未入力エラー処理 ===
            print("--- DEBUG: FORM IS NOT VALID. ERRORS BELOW ---")
            print(form.errors) 
            print("---------------------------------------------")
            
            logger.error("PhotoPostForm validation failed: %s", form.errors)
            messages.error(request, "投稿内容にエラーがあります。不足している必須項目（写真、カテゴリ、タイトル）を確認するか、写真のファイルサイズ（最大5MB）を確認してください。")
    
    # GETリクエスト、またはPOST失敗時
    else:
        # ... (中略：initialデータ設定ロジック - 変更なし)
        
        initial_data = post_data.copy()
        
        # ★修正: セッションに保存された単一のPKをModelChoiceFieldが期待するインスタンスに変換し直す★
        tag_pk = initial_data.get('tags') # 修正: 単一PKとして取得
        if tag_pk:
            try:
                # ModelChoiceFieldがPKを受け付けるので、Tagインスタンスを渡す
                # ModelChoiceFieldは単一のインスタンスを期待する
                initial_data['tags'] = models.Tag.objects.get(pk=tag_pk) # ここも修正
            except models.Tag.DoesNotExist:
                initial_data['tags'] = None
            except Exception:
                initial_data['tags'] = None
                
        form = PhotoPostForm(initial=initial_data)
        print("--- DEBUG: Rendering Step 1 Form ---") # GETリクエストの確認
    
    # ② システムは投稿画面を表示する
    return render(request, 'main/photo_post_create.html', {'form': form, 'step': 1})


@login_required
def photo_post_manual_location(request):
    """基本フロー⑤/代替④ - 報告作成ステップ2: 位置情報の確認・手動設定"""
    post_data = request.session.get('post_data')
    
    # ステップ1のデータがない場合、最初のステップに戻す
    if not post_data:
        messages.error(request, "報告のデータが見つかりませんでした。最初からやり直してください。")
        return redirect('photo_post_create')
    
    if request.method == 'POST':
        # 代替フロー④-2: 手動入力フォームからのPOST
        # ManualLocationFormはlocation_nameを扱うフォームとして想定します。
        form = ManualLocationForm(request.POST)
        if form.is_valid():
            # location_nameをセッションデータに追加・更新
            post_data.update(form.cleaned_data)
            request.session['post_data'] = post_data
            
            # 代替フロー④-3: 投稿内容確認画面へリダイレクト
            return redirect('photo_post_confirm')
        else:
            # バリデーションに失敗した場合
            messages.error(request, "入力された地名が正しくありません。") 

    else:
        # GETリクエストの場合
        form = ManualLocationForm(initial=post_data)
        
    context = {
        'manual_form': form, 
        'post_data': post_data,
        'step': 2
    }
    return render(request, 'main/photo_post_manual_location.html', context)

@login_required
def photo_post_confirm(request):
    """基本フロー⑥/⑦/⑧ - 報告作成ステップ3: 最終確認と保存"""
    post_data = request.session.get('post_data')
    photo_file_data = request.session.get('post_photo_data') 

    # データを取得できていない場合、ステップ1に戻る
    if not post_data:
        messages.error(request, "データが不足しています。最初からやり直してください。")
        return redirect('photo_post_create')
    
    # 【位置情報の上書き/確認】
    latitude_query = request.GET.get('latitude')
    longitude_query = request.GET.get('longitude')
    
    if latitude_query and longitude_query:
        post_data['latitude'] = latitude_query
        post_data['longitude'] = longitude_query
        request.session['post_data'] = post_data
        logger.info("--- GEOLOCATION SUCCESS: Location data updated from query params. ---")
    
    # 基本フロー⑦: POSTリクエスト（「この内容で投稿する」）
    if request.method == 'POST':
        try:
            # 緯度・経度の値を取得
            def safe_float(value):
                try:
                    return float(value)
                except (ValueError, TypeError):
                    # null=True, blank=Trueなので、Noneを返すことでDBのNULLを許容する
                    return None 
            
            latitude_val = safe_float(post_data.get('latitude'))
            longitude_val = safe_float(post_data.get('longitude'))
            
            # 1. セッションデータからインスタンスを作成
            new_post = models.PhotoPost(
                user=request.user,
                # ★修正: セッションに保存されたtitleを利用する
                title=post_data.get('title'), 
                comment=post_data.get('comment'),
                latitude=latitude_val, 
                longitude=longitude_val, 
                location_name=post_data.get('location_name', '')
            )
            
            # 2. 画像ファイルの再構築とインスタンスへのセット
            if photo_file_data:
                # Latin-1でエンコードされた文字列を再度バイトに変換
                file_content = photo_file_data['content'].encode('latin-1') 
                reconstructed_file = SimpleUploadedFile(
                    name=photo_file_data['name'],
                    content=file_content,
                    content_type=photo_file_data['content_type']
                )
                new_post.photo = reconstructed_file
            
            # 3. モデルの検証と保存
            new_post.full_clean()
            new_post.save()
            
            # 4. ManyToManyField (タグ) を保存 (単一選択ロジック)
            tag_pk = post_data.get('tags') 
            if tag_pk:
                try:
                    # 単一のPKからTagインスタンスを取得
                    tag_instance = models.Tag.objects.get(pk=tag_pk)
                    # set() メソッドは単一の要素でもリストで渡す
                    new_post.tags.set([tag_instance]) 
                except models.Tag.DoesNotExist:
                    logger.warning(f"投稿保存時にタグID {tag_pk} が見つかりませんでした。タグなしで保存されます。")
                    new_post.tags.clear()
            else:
                new_post.tags.clear()
            
            # 5. 成功したらセッションデータをクリア
            del request.session['post_data']
            if 'post_photo_data' in request.session:
                del request.session['post_photo_data']
            
            # 6. 完了画面へリダイレクト（基本フロー⑧）
            messages.success(request, "報告を送信しました。")
            return redirect('photo_post_done')
            
        except ValidationError as e:
            # データ検証エラー：緯度経度以外のエラー
            error_messages = "\n".join([f"「{k}」: {v[0]}" for k, v in e.message_dict.items()])
            messages.error(request, f"**データ検証エラー**：投稿の保存に必要な情報が不足しています。不足フィールド:\n{error_messages}")
            
            # エラー発生時はステップ1に戻す
            return redirect('photo_post_create')
            
        except Exception as e:
            # 代替フロー②：投稿時に通信エラーが発生した場合
            logger.error("--- FATAL ERROR: 報告保存時の予期せぬ一般エラーが発生 ---", exc_info=True)
            messages.error(request, f"**投稿通信エラー**：報告の保存中に予期せぬエラーが発生しました。再度投稿してください。エラー: {e}")
            return redirect('photo_post_create')
            
    # GETリクエスト時 (確認画面の表示)
    # ★修正: 確認画面表示のため、単一のPKからTagインスタンスに戻す★
    tag_pk = post_data.get('tags')
    selected_tag = None
    if tag_pk:
        try:
            selected_tag = models.Tag.objects.get(pk=tag_pk)
        except models.Tag.DoesNotExist:
            logger.error(f"確認画面でタグID {tag_pk} が見つかりません。")
            pass
            
    context = {
        'post_data': post_data,
        'selected_tag': selected_tag, # テンプレートで表示するために追加
        'step': 3
    }
    return render(request, 'main/photo_post_confirm.html', context)

@login_required
def photo_post_done(request):
    """報告作成完了（基本フロー⑧）"""
    return render(request, 'main/photo_post_complete.html', {})


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
    return render(request, 'main/admin_home.html', context)




@user_passes_test(is_staff_user, login_url='/')
def admin_user_list(request):
    """管理者向けユーザー一覧表示画面"""
    User = get_user_model()
    # 自分自身（リクエストユーザー）以外の全ユーザーを取得し、登録が新しい順に並べ替え
    users = User.objects.exclude(pk=request.user.pk).order_by('-date_joined')
    
    context = {
        'users': users,
        'app_name': 'ユーザー一覧'
    }
    # テンプレートは admin_user_list.html を使用
    return render(request, 'main/admin_user_list.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_user_delete_confirm(request, user_id):
    """特定のユーザーを削除する処理 (POSTのみ許可)"""
    User = get_user_model()

    # GETリクエストは一覧に戻す (削除確認はモーダルで行うため)
    if request.method == 'GET':
        return redirect('admin_user_list')
    
    # POSTリクエスト: 削除処理を実行
    if request.method == 'POST':
        # 削除対象のユーザーを取得 (存在しない場合は404)
        user_to_delete = get_object_or_404(User, pk=user_id)
        
        # 自身を削除しようとしていないかチェック
        if user_to_delete.pk == request.user.pk:
            messages.error(request, "自分自身のアカウントをこの画面から削除することはできません。")
            return redirect('admin_user_list')
        
        try:
            # ユーザーを削除
            username = user_to_delete.username
            user_to_delete.delete()
            
            messages.success(request, f"ユーザー「{username}」を削除しました。")
            # 成功したら削除完了画面へリダイレクト
            return redirect('admin_user_delete_complete')
            
        except Exception as e:
            # データの整合性エラーやその他の予期せぬエラー
            logger.error(f"ユーザーID {user_id} の削除中にエラーが発生: {e}", exc_info=True)
            messages.error(request, f"削除中に予期せぬエラーが発生しました。詳細: {e}")
            return redirect('admin_user_list')

# NOTE: ここにあった admin_user_delete_confirm の重複定義を削除しました。

@user_passes_test(is_staff_user, login_url='/')
def admin_user_delete_complete(request):
    """ユーザー削除完了画面"""
    # テンプレートは admin_user_delete_complete.html を使用
    context = {
        'app_name': '削除完了'
    }
    return render(request, 'main/admin_user_delete_complete.html', context)


# --- 管理者向け：報告の確認・記録機能 ---

@user_passes_test(is_staff_user, login_url='/')
def admin_post_list(request):
    """
    管理者向けの報告一覧ビュー。
    ステータス、タグ、優先度で絞り込みを可能にする。
    """
    status_filter = request.GET.get('status', None)
    tag_filter = request.GET.get('tag', None)
    priority_filter = request.GET.get('priority', None)

    # PhotoPostをベースに、ユーザーとタグのデータをプリフェッチして効率化
    posts = models.PhotoPost.objects.all().select_related('user').prefetch_related('tags').order_by('-posted_at')

    # 1. ステータスによる絞り込み
    valid_statuses = dict(models.PhotoPost.STATUS_CHOICES).keys()
    if status_filter in valid_statuses:
        posts = posts.filter(status=status_filter)

    # 2. タグによる絞り込み
    if tag_filter:
        try:
            # タグIDが整数であることを確認
            tag_id = int(tag_filter)
            posts = posts.filter(tags__id=tag_id)
        except ValueError:
            # フィルター値が無効な場合は無視
            pass

    # 3. 優先度による絞り込み (未設定（__none__）に対応)
    if priority_filter:
        if priority_filter == '__none__':
            # 優先度が未設定（NULL）の投稿をフィルタリング
            posts = posts.filter(priority__isnull=True)
        else:
            # 'low', 'medium', 'high'のいずれかでフィルタリング
            posts = posts.filter(priority=priority_filter)

    # 全タグを取得（フォームの選択肢用）
    all_tags = models.Tag.objects.all().order_by('name')

    context = {
        'posts': posts,
        'status_filter': status_filter,
        'tag_filter': tag_filter,
        'priority_filter': priority_filter,
        'all_tags': all_tags,
    }
    # テンプレート名を 'admin_post_list.html' に変更
    return render(request, 'main/admin_post_list.html', context)

@user_passes_test(is_staff_user, login_url='/')
def admin_post_detail(request, post_id):
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    # status編集用のフォームを追加
    form = StatusUpdateForm(instance=post)
    context = {
        'post': post,
        'form': form
    }
    return render(request, 'main/admin_post_detail.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_post_status_edit(request, post_id):
    post = get_object_or_404(models.PhotoPost, pk=post_id)

    if request.method == 'POST':
        form = StatusUpdateForm(request.POST, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)

            # completed_atフィールドがないため、このロジックはコメントアウトするか、モデルにcompleted_atフィールドを追加してください
            # if updated_post.status == 'completed' and not updated_post.completed_at:
            #     updated_post.completed_at = timezone.now()
            #
            # elif updated_post.status != 'completed' and updated_post.completed_at:
            #     updated_post.completed_at = None

            updated_post.save()
            messages.success(request, f"報告 (ID: {post_id}) のステータスを更新しました。")
            return redirect('admin_status_edit_done', post_id=post.pk)
    else:
        form = StatusUpdateForm(instance=post)

    context = {
        'form': form,
        'post': post
    }
    return render(request, 'main/admin_post_status_edit.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_status_edit_done(request, post_id):
    """ステータス編集完了画面"""
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    context = {'post': post}
    return render(request, 'main/admin_status_complete.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_post_delete(request, post_id):
    """管理者向け：報告の削除処理 (POST専用)"""
    post = get_object_or_404(models.PhotoPost, pk=post_id)

    if request.method == 'POST':
        # 削除前の報告情報を取得し、メッセージに利用
        post_pk = post.pk
        # コメントの先頭20文字を報告タイトルとして使用
        post_title = (post.comment[:20] + '...') if post.comment and len(post.comment) > 20 else post.comment or f"ID:{post_pk}の報告"

        try:
            post.delete()

            messages.success(request, f"報告「{post_title}」を削除しました。")

            # ★修正: 削除完了後、一覧ではなく新しい完了画面にリダイレクト★
            return redirect('admin_post_delete_complete')

        except Exception as e:
            logger.error(f"報告ID {post_id} の削除中にエラーが発生: {e}", exc_info=True)
            messages.error(request, "報告の削除中に予期せぬエラーが発生しました。")
            return redirect('admin_post_detail', post_id=post_id)

    # POST以外のリクエストは詳細画面に戻す
    messages.error(request, "報告の削除にはPOSTリクエストが必要です。")
    return redirect('admin_post_detail', post_id=post_id)


@user_passes_test(is_staff_user, login_url='/')
def admin_post_delete_complete(request):
    """
    ★新規追加: 管理者向け：報告削除完了画面
    ユーザー削除完了画面(admin_user_delete_complete)に倣い、シンプルな完了画面とします。
    """
    context = {
        'app_name': '報告削除完了'
    }
    return render(request, 'main/admin_post_delete_complete.html', context)
