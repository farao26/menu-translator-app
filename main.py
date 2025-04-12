import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
from streamlit_extras.let_it_rain import rain

# SecretsからAPIキー取得
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

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

# ページスタイル調整
st.set_page_config(page_title="Menu OCR & Translation", layout="wide")
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url('https://images.unsplash.com/photo-1550985607-b2839a9b27c6');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}
[data-testid="stSidebar"] {
    background-color: rgba(255,255,255,0.8);
}
.block-container {
    background-color: rgba(255,255,255,0.8);
    border-radius: 12px;
    padding: 2rem;
    backdrop-filter: blur(10px);
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# アプリ本体
st.title("📖 Menu OCR & 翻訳")
st.caption("画像から日本語メニューを読み取り、英語へ翻訳します。")

uploaded_file = st.file_uploader("📷 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.subheader("🔍 OCR 抽出結果")
    text = ocr_with_google_vision(image)
    st.text_area("抽出された日本語テキスト", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌐 翻訳結果（番号付きで対応表示）")
        for i, line in enumerate(lines, start=1):
            with st.container():
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**{i}. 🍽️ {line}**")
                with col2:
                    translation = translate_text_deepl(line)
                    st.markdown(f"➡️ {translation}")
    else:
        st.warning("テキストが認識されませんでした。画像をご確認ください。")