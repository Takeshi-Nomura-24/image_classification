import numpy as np
import cv2
import base64
from django.apps import apps
from django.shortcuts import render
from keras.applications.vgg16 import preprocess_input, decode_predictions

def index(request):
    context = {}
    if request.method == "POST" and request.FILES.get("imageFile"):
        file = request.FILES["imageFile"]

        try:
            # 1. OpenCVでメモリ上で読み込む (ディスク保存をスキップ)
            file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
            img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # 2. VGG16用の前処理
            # OpenCVはBGR、Keras(VGG16)はRGBを期待するため変換
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_res = cv2.resize(img_rgb, (224, 224))
            
            x = np.expand_dims(img_res, axis=0)
            x = preprocess_input(x.astype(np.float32))

            # 3. ロード済みモデルの取得
            app_config = apps.get_app_config('image_classification')
            model = app_config.image_model
            
            if model is None:
                # from tensorflow.keras.applications.vgg16 import VGG16
                from keras.applications.vgg16 import VGG16
                model = VGG16(weights='imagenet')

            # 4. 推論
            preds = model.predict(x)
            decoded_results = decode_predictions(preds, top=3)[0]

            # 5. 結果をリストにまとめて洗練化
            predictions = []
            for _, name, prob in decoded_results:
                predictions.append({
                    "name": name.replace('_', ' ').capitalize(), # ラベルを見やすく整形
                    "prob": f"{prob:.2%}",
                    "raw_prob": prob * 100 # CSSのバーなどで使う用
                })

            # 6. 表示用に画像をBase64文字列に変換
            _, buffer = cv2.imencode('.jpg', img_bgr)
            img_str = base64.b64encode(buffer).decode('utf-8')

            context = {
                "predictions": predictions,
                "image_data": f"data:image/jpeg;base64,{img_str}",
            }

        except Exception as e:
            print(f"Error: {e}")
            context = {"error_msg": "画像の解析に失敗しました。形式を確認してください。"}

    return render(request, "index.html", context)
