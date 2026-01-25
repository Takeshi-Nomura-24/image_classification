import io
import os
import numpy as np
import cv2
import gc  # ガベージコレクション（メモリ解放用）
from django.shortcuts import render, redirect, get_object_or_404
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.conf import settings

# MobileNetV2専用の処理をインポート
from keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from .models import AnalysisResult

def index(request):
    predictions = None
    image_url = None

    if request.method == 'POST' and request.FILES.get('imageFile'):
        # 0. 解析前に一度メモリを掃除
        gc.collect()

        try:
            # 1. 画像読み込みとリサイズ
            file = request.FILES['imageFile']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # リサイズを先に行い、メモリ消費を抑える
            img_resized = cv2.resize(img, (224, 224))
            
            # 不要なオリジナル画像のメモリを即座に解放
            del img, file_bytes
            
            # 2. 推論用データの作成
            x = np.expand_dims(img_resized, axis=0)
            x = preprocess_input(x.astype(np.float32))

            # 3. AI推論実行
            model = apps.get_app_config('predict').model
            preds = model.predict(x)
            results = decode_predictions(preds, top=5)[0]

            # 4. 解析完了直後に重いデータを削除
            del x, img_resized
            gc.collect()

            # 5. 結果の整形（英語名のまま）
            predictions = []
            for class_id, name, prob in results:
                display_name = name.replace('_', ' ')
                predictions.append({
                    'name': display_name,
                    'prob': f"{prob * 100:.2f}%",
                    'raw_prob': prob * 100
                })

            # 6. データベース保存
            top_id, top_name, top_prob = results[0]
            save_name = top_name.replace('_', ' ')
            
            file.seek(0)
            result_instance = AnalysisResult(
                image=file,
                prediction_label=save_name,
                prediction_score=round(float(top_prob * 100), 2)
            )
            result_instance.save()
            image_url = result_instance.image.url

        except Exception as e:
            print(f"Error during analysis: {e}")
            # エラー時もメモリを掃除
            gc.collect()

    return render(request, 'index.html', {
        'predictions': predictions,
        'image_data': image_url
    })

def view_data(request):
    all_results = AnalysisResult.objects.all().order_by('-created_at')
    paginator = Paginator(all_results, 10)
    page_number = request.GET.get('page')
    results = paginator.get_page(page_number)
    return render(request, 'view_data.html', {'results': results})

def delete_data(request, pk):
    result = get_object_or_404(AnalysisResult, pk=pk)
    result.delete()
    return redirect('predict:view_data')


