import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# 環境変数読み込み（Streamlit Cloudではsecretsを使用）
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# Google Cloud Vision OCR関数
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

# DeepL翻訳関数
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

# UI セットアップ
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    body {
        background: linear-gradient(145deg, #001f3f, #1a1a2e);
        color: white;
    }
    .card {
        transition: transform .2s;
        background-color: #00334e;
        color: #fff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .card:hover {
        transform: scale(1.05);
        background-color: #004b6b;
    }
    a {
        color: #66ccff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍷 Elegant Menu Translator")
st.write("メニュー画像をアップロードして、日本語を英語に翻訳します")

uploaded_file = st.file_uploader("📸 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

# 翻訳履歴保存用
if "history" not in st.session_state:
    st.session_state.history = []

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロード画像", use_column_width=True)
    st.markdown("---")

    # OCR
    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 翻訳結果（カード＋ホバー拡大）")
        for line in lines:
            translated = translate_text_deepl(line)
            st.session_state.history.append((line, translated))
            
            query = translated.replace(" ", "+")
            search_url = f"https://www.google.com/search?tbm=isch&q={query}"

            st.markdown(f"""
            <div class="card">
                <b>{line}</b><br>
                <span style='color:#ccffcc;'>➡️ {translated}</span><br>
                <a href="{search_url}" target="_blank">🔍 この料理を画像検索</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")

# 翻訳履歴の保存
if st.session_state.history:
    if st.button("💾 翻訳履歴を保存"):
        filename = f"translation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for original, translated in st.session_state.history:
                f.write(f"{original} => {translated}\n")
        with open(filename, "rb") as f:
            st.download_button("⬇️ ダウンロード", f, file_name=filename)

