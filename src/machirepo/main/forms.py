from django import forms
from django.contrib.auth import get_user_model 
from django.core.validators import MinLengthValidator
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import PhotoPost, Tag 
from . import models 

User = get_user_model() 
Resident = get_user_model()

# 1. 新規登録フォーム (ResidentCreationForm)

class ResidentCreationForm(forms.ModelForm): # ModelFormを継承
    username = forms.CharField(
        label='氏名',
        max_length=150,
        help_text='150文字以内で入力してください。',
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
    
    password = forms.CharField(
        label='パスワード', 
        widget=forms.PasswordInput,
        max_length=128
    )
  


    agree_terms = forms.BooleanField(
        label='利用規約に同意する',
        required=True,
        error_messages={'required': '利用規約への同意が必要です。'}
    )



    class Meta:
        model = User
        fields = ('username', 'email') 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            if 'last_name' in self.fields:
                self.fields['last_name'].required = False
            if 'first_name' in self.fields:
                self.fields['first_name'].required = False
        
        common_attrs = {
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
        }
        
        for name, field in self.fields.items():
            field.widget.attrs.update(common_attrs)
    
    def clean_agree_terms(self):
        if not self.cleaned_data.get('agree_terms'):
            raise ValidationError('利用規約に同意してください。')
        return True


    def clean(self):
        cleaned_data = super().clean()
        
        password = cleaned_data.get('password')
        email = cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            self.add_error('email', "このメールアドレスは既に使用されています。")

        return cleaned_data
        
    def save(self, commit=True):
        user = User(
            username=self.cleaned_data["username"], 
            email=self.cleaned_data["email"],
            is_staff=False,
            is_superuser=False,
        )
        
        password = self.cleaned_data["password"]
        user.set_password(password)
        
        if commit:
            user.save() 
        return user




# 2. ログインフォーム (EmailAuthenticationForm)
class EmailAuthenticationForm(AuthenticationForm):
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
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            user = None

        if user is not None and user.check_password(password):
            self.user_cache = user
            
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
        else:
            raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')

        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'badge_rank')  
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'badge_rank': forms.RadioSelect(attrs={'class': 'hidden-radio'}),
        }
    
    def __init__(self, *args, **kwargs):
        badge_choices = kwargs.pop('badge_choices', [('none', '表示しない')])
        super().__init__(*args, **kwargs)
        self.fields['badge_rank'].choices = badge_choices

        if self.instance.badge_rank not in [b[0] for b in badge_choices]:
            self.initial['badge_rank'] = 'none'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("このユーザー名は既に使用されています。")
        return username
    




# 3. 投稿作成フォーム (PhotoPostForm)

class PhotoPostForm(forms.ModelForm):
    title = forms.CharField(
        label="報告のタイトル", 
        max_length=100,
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': '例：〇〇公園のベンチが壊れている', }),
        error_messages={
            'required': '報告のタイトルは必須です。', 
        }
    )

    tag = forms.ModelChoiceField(
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
        fields = ('title', 'photo', 'tag', 'comment', 'latitude', 'longitude')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['latitude'].required = False 
        self.fields['longitude'].required = False 
        
        self.fields['photo'].label = "写真 (必須)"
        self.fields['photo'].error_messages = {'required': '写真をアップロードしてください。'}

        for name, field in self.fields.items():
            if name not in ['tag', 'photo', 'latitude', 'longitude']:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
                })
            elif name == 'photo':
                field.widget.attrs.update({
                    'class': 'input-file-trick'
                })
            elif name == 'tag':
                field.widget.attrs.update({
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
                })




# 4. 位置情報手動入力フォーム (ManualLocationForm)
    
class ManualLocationForm(forms.Form):
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
    
    



# 5. 管理者向け：ステータス更新フォーム (StatusUpdateForm)
class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = PhotoPost
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
    name = forms.CharField(max_length=50) 
    
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': '例：ゴミ問題',
                'required': 'required',
            })
        }