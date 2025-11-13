from django import forms
from django.contrib.auth import get_user_model 
from django.core.validators import MinLengthValidator
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import PhotoPost, Tag 
from . import models 

# settings.pyで指定されたユーザーモデルを取得
User = get_user_model() 
Resident = get_user_model()
# -----------------------------------------------------
# 1. 新規登録フォーム (ResidentCreationForm)
# -----------------------------------------------------

class ResidentCreationForm(forms.ModelForm): # ModelFormを継承
    # Userモデルのusernameフィールドを氏名として再定義（ニックネームとして使用）
    username = forms.CharField(
        label='氏名',
        max_length=50,
        help_text='50文字以内で入力してください。',
        error_messages={
            'required': '氏名は必須です。',
            'max_length': '氏名は50文字以内で入力してください。' 
        }
    )

    email = forms.EmailField(
        label='メールアドレス', 
        max_length=254, 
        required=True
    )
    
    # パスワードフィールドをカスタムで追加
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    # 💡 修正点: password2 フィールドを削除しました
    # password2 = forms.CharField(label='パスワード（確認）', widget=forms.PasswordInput)


    class Meta:
        model = User
        # passwordはカスタムフィールドとしてクラス内で定義されているため、
        # ここには含めず、ModelFormの自動生成対象から外します。
        fields = ('username', 'email') 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 💡 AbstractUserのフィールドがModelFormによって生成された場合でも、
        # CustomUserには不要なので非必須として無視します。
        if not self.instance.pk:
            if 'last_name' in self.fields:
                self.fields['last_name'].required = False
            if 'first_name' in self.fields:
                self.fields['first_name'].required = False
        
        # スタイル設定
        common_attrs = {
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
        }
        
        # 💡 修正点: password2 が削除されたため、このループは問題なく動作します
        for name, field in self.fields.items():
            field.widget.attrs.update(common_attrs)

    # ------------------------------------------------------------------
    # clean(): バリデーションとパスワードの一致チェック
    # ------------------------------------------------------------------
    def clean(self):
        cleaned_data = super().clean()
        # 💡 修正点: password2 の取得と一致チェックを削除しました
        password = cleaned_data.get('password')
        email = cleaned_data.get('email')

        # 💡 emailの重複チェック
        if email and User.objects.filter(email__iexact=email).exists():
            self.add_error('email', "このメールアドレスは既に使用されています。")

        return cleaned_data
        
    # ------------------------------------------------------------------
    # save()メソッド: パスワードのハッシュ化とUserモデルの保存 (強制ロジック)
    # ------------------------------------------------------------------
    def save(self, commit=True):
        # ModelFormのsave()に頼らず、Userインスタンスを直接作成
        user = User(
            username=self.cleaned_data["username"], 
            email=self.cleaned_data["email"],
            is_staff=False,
            is_superuser=False,
        )
        
        # パスワードをハッシュ化して設定
        password = self.cleaned_data["password"]
        user.set_password(password)
        
        # データベースに保存
        if commit:
            user.save() 
        return user



# -----------------------------------------------------
# 2. ログインフォーム (EmailAuthenticationForm)
# -----------------------------------------------------
class EmailAuthenticationForm(AuthenticationForm):
    """
    ユーザー名ではなくメールアドレスで認証を行うフォーム。
    """
    error_messages = {
        'invalid_login': 'メールアドレスまたはパスワードが正しくありません。',
        'inactive': 'このアカウントは非アクティブです。'
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'メールアドレス'
        self.error_css_class = 'is-invalid'

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not username or not password:
            raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
            
        try:
            # メールアドレスでユーザーを検索
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            user = None

        if user is not None and user.check_password(password):
            self.user_cache = user
            
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
        else:
            # 認証失敗（ユーザー不在 or パスワード間違い）
            raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')

        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)
    


User = get_user_model()

# 🌟 新規追加: ユーザー名とメールアドレス編集用フォーム
class UserUpdateForm(forms.ModelForm):
    # パスワードは別の画面で変更するため、含めない
    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }
    
    # バリデーションの例: ユーザー名が一意であることを確認
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # 自身を除く他のユーザーで同じユーザー名が存在するかチェック
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
             raise forms.ValidationError("このユーザー名は既に使用されています。")
        return username




# -----------------------------------------------------
# 3. 投稿作成フォーム (PhotoPostForm)
# -----------------------------------------------------
class PhotoPostForm(forms.ModelForm):
    # titleフィールドを明示的に定義し、必須チェックとカスタムエラーメッセージを設定
    title = forms.CharField(
        label="報告のタイトル", 
        max_length=100,
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': '例：〇〇公園のベンチが壊れている', 'maxlength': 100}),
        error_messages={
            'required': '報告のタイトルは必須です。', 
            'max_length': 'タイトルは100文字以内で入力してください。'
        }
    )

    tags = forms.ModelChoiceField(
        queryset=models.Tag.objects.all().order_by('name'),
        empty_label="カテゴリーを選択してください",
        label="カテゴリ",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True 
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': '例：座る部分が壊れていて危険です。'}),
        required=True, 
        label="状況説明"
    )

    class Meta:
        model = models.PhotoPost 
        # photoは必須。latitude, longitudeは次のステップで入力されるため、ここでは非必須扱い。
        fields = ('title', 'photo', 'tags', 'comment', 'latitude', 'longitude')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 緯度・経度は後のステップで入力されるため、ここでは非必須
        self.fields['latitude'].required = False 
        self.fields['longitude'].required = False 
        
        # photoフィールドのラベルを修正
        self.fields['photo'].label = "写真 (必須)"
        self.fields['photo'].error_messages = {'required': '写真をアップロードしてください。'}

        # CSSクラスの適用
        for name, field in self.fields.items():
            if name not in ['tags', 'photo', 'latitude', 'longitude']:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
                })
            elif name == 'photo':
                field.widget.attrs.update({
                    'class': 'w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'
                })
            elif name == 'tags':
                field.widget.attrs.update({
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
                })



# -----------------------------------------------------
# 4. 位置情報手動入力フォーム (ManualLocationForm)
# -----------------------------------------------------
    
class ManualLocationForm(forms.Form):
    """基本フロー② - 位置情報の手動入力フォーム（★コメント入力専用に変更★）"""
    # comment = forms.CharField(
    #     label="詳細情報（必須）",
    #     required=True,
    #     widget=forms.Textarea(attrs={'rows': 5, 'placeholder': '例: 交差点の北西角が陥没しています。発生時期は不明です。'}),
    #     help_text="具体的な状況や発生時期、危険性などを詳しく記述してください。",
    #     validators=[MinLengthValidator(10, message='詳細情報は10文字以上で入力してください。')]
    # )

    location_name = forms.CharField(
        label="地名（任意）", 
        max_length=255, 
        required=True,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': '例: 交差点の北西角が陥没しています。発生時期は不明です。'}) # 2行分の高さを指定
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
            })
    
    


# -----------------------------------------------------
# 5. 管理者向け：ステータス更新フォーム (StatusUpdateForm)
# -----------------------------------------------------
class StatusUpdateForm(forms.ModelForm):
    """
    管理者による報告ステータスと優先順位の更新に使用するフォーム
    """
    class Meta:
        model = PhotoPost
        # 💡 PhotoPostモデルのフィールドを参照
        fields = ('status', 'priority', 'admin_note')
        labels = {
            'status': '対応ステータス',
            'priority': '対応優先順位',
            'admin_note': '対応内容/判断結果（住民公開用コメント）', # ラベルを詳細化
        }
        widgets = {
            'admin_note': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'priority': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
        }


class TagForm(forms.ModelForm):
    """タグ新規作成用のフォーム"""
    class Meta:
        model = Tag
        # nameフィールドのみを使用
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': '例：ゴミ問題',
                'required': 'required',
            })
        }