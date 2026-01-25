import os
import numpy as np
import cv2
import gc
from django.shortcuts import render, redirect, get_object_or_404
from django.apps import apps
from django.core.paginator import Paginator
from django.conf import settings
from .models import AnalysisResult

def index(request):
    predictions = None
    image_url = None

    if request.method == 'POST' and request.FILES.get('imageFile'):
        try:
            # 1. 画像の取得とOpenCV形式への変換
            file = request.FILES['imageFile']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # 2. 前処理: 224x224へリサイズ & RGB変換
            img_resized = cv2.resize(img, (224, 224))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            
            # 3. MobileNetV2用の正規化 (x / 127.5 - 1.0)
            # 浮動小数点数32bitに変換して計算
            x = img_rgb.astype(np.float32)
            x = (x / 127.5) - 1.0
            x = np.expand_dims(x, axis=0)  # 四次元配列へ [1, 224, 224, 3]

            # 4. ONNX推論実行
            config = apps.get_app_config('predict')
            if config.session is None:
                raise Exception("ONNX model not loaded.")
                
            # 推論実行
            ort_inputs = {config.input_name: x}
            preds = config.session.run(None, ort_inputs)[0] # 出力は [1, 1000] の配列

            # 5. 結果の整形 (Softmaxを手動計算して確率を出す)
            # 指数関数を計算して合計で割る（数値安定性のためにmaxを引く）
            e_x = np.exp(preds[0] - np.max(preds[0]))
            probs = e_x / e_x.sum()
            
            # 上位5件のインデックスを取得
            top_5_indices = np.argsort(probs)[-5:][::-1]
            
            # 表示用データの作成（英語名の取得。本来はImageNetラベルリストが必要）
            # ここでは簡単のため「Class [ID]」として表示します
            predictions = []
            for idx in top_5_indices:
                predictions.append({
                    'name': f"Class ID: {idx}", # ここをラベル名にする方法は下記参照
                    'prob': f"{probs[idx] * 100:.2f}%",
                    'raw_prob': probs[idx] * 100
                })

            # 6. データベースへの保存処理
            top_idx = top_5_indices[0]
            top_prob = probs[top_idx]
            
            file.seek(0)
            result_instance = AnalysisResult(
                image=file,
                prediction_label=f"Class {top_idx}",
                prediction_score=round(float(top_prob * 100), 2)
            )
            result_instance.save()
            image_url = result_instance.image.url

            # メモリ解放
            del img, img_resized, img_rgb, x, preds, probs
            gc.collect()

        except Exception as e:
            print(f"Prediction Error: {e}")
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


