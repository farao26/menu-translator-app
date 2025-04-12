import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
from streamlit_extras.let_it_rain import rain

# 背景をカフェ風に設定
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1509042239860-f550ce710b93');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: #333;
    }
    .ocr-line {
        padding: 10px;
        margin-bottom: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ocr-line h4 {
        margin: 0;
    }
    .ocr-line p {
        margin: 0;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 環境変数の読み込み
load_dotenv()
GOOGLE_CLOUD_VISION_API_KEY = st.secrets.get("GOOGLE_CLOUD_VISION_API_KEY")
DEEPL_API_KEY = st.secrets.get("DEEPL_API_KEY")

# Google Cloud Vision API を使って OCR を実行する関数
def ocr_with_google_vision(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = {
        "requests": [
            {
                "image": {"content": img_base64},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["ja"]}
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        annotations = response.json()["responses"][0].get("textAnnotations")
        if annotations:
            return annotations[0]["description"]
        else:
            return ""
    else:
        return f"[Error] {response.status_code}: {response.text}"

# DeepL API を使った翻訳関数
def translate_text_deepl(text, source_lang='JA', target_lang='EN'):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    else:
        return f"[Error] {response.status_code}: {response.text}"

# Streamlit アプリ本体
st.title("📸 Menu OCR & 翻訳（Google Vision + DeepL）")
uploaded_file = st.file_uploader("画像をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.subheader("🔍 Google Cloud Vision OCR結果")
    text = ocr_with_google_vision(image)
    st.text_area("抽出された日本語テキスト", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌍 DeepL 翻訳結果")
        for line in lines:
            with st.container():
                st.markdown(f"""
                <div class="ocr-line">
                    <h4>🍽️ {line}</h4>
                    <p>➡️ {translate_text_deepl(line)}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")