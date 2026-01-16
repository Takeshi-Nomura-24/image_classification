import os
from pathlib import Path
import dj_database_url # 💡 これを追記


# 1. パスの設定
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. セキュリティ設定
SECRET_KEY = 'django-insecure-ks08+v=vkc+h#=@ia!3_h=590()bsm$b0dwb2n2c@*yjb0%@hu'
DEBUG = True
ALLOWED_HOSTS = ['*']  # 開発用に全て許可

# 3. アプリケーション定義
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # プロジェクト名.apps.クラス名
    'predict.apps.PredictConfig'
]

# 4. ミドルウェア（エラーの核心部分：順番が重要）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # adminに必須
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # adminに必須
    'django.contrib.messages.middleware.MessageMiddleware',      # adminに必須
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 5. URLとWSGIの設定
ROOT_URLCONF = 'image_classification.urls'
WSGI_APPLICATION = 'image_classification.wsgi.application'

# 6. テンプレートの設定
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # プロジェクトフォルダ内のtemplatesフォルダを指定
        'DIRS': [BASE_DIR  / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(default=os.environ['DATABASE_URL'], conn_max_age=600)
    }
else:
    # ローカル開発用のSQLite設定（必要に応じて残すか削除）
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# 8. パスワードバリデーション（開発中はデフォルトのまま）
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# 9. 言語・タイムゾーン設定
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# 10. 静的ファイルとメディアファイルの設定
STATIC_URL = 'static/'
# 警告回避のため、フォルダが存在する場合のみ設定
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

import os

# 11. デフォルトのID型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
