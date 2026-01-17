import os
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from .models import Prediction
# 軽量なMobileNetV2をインポート
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import numpy as np

# サーバー起動時に一度だけモデルをロード（メモリ節約のため）
# weights='imagenet' で学習済みデータをダウンロードします
model = MobileNetV2(weights='imagenet')

def predict(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 画像の保存
            instance = form.save()
            img_path = os.path.join(settings.MEDIA_ROOT, instance.image.name)

            # 画像の読み込みと前処理
            img = image.load_img(img_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # AI推論の実行
            preds = model.predict(img_array)
            # 解析結果のデコード（上位3つを取得）
            results = decode_predictions(preds, top=3)[0]

            # 最も確率が高い結果を保存
            instance.prediction_label = results[0][1] # カテゴリ名
            instance.prediction_score = float(results[0][2]) # 確率
            instance.save()

            return render(request, 'predict/result.html', {
                'prediction': instance,
                'all_predictions': results,
            })
    else:
        form = ImageUploadForm()
    
    # 履歴を表示するためにすべてのデータを取得（新しい順）
    history = Prediction.objects.all().order_by('-created_at')
    return render(request, 'predict/index.html', {'form': form, 'history': history})

def delete_prediction(request, pk):
    """履歴を削除するための関数"""
    prediction = Prediction.objects.get(pk=pk)
    # 画像ファイル自体も削除する場合（任意）
    if prediction.image:
        if os.path.isfile(prediction.image.path):
            os.remove(prediction.image.path)
    prediction.delete()
    return redirect('predict')