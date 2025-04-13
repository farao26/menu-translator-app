import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
import re

# SecretsからAPIキー読み込み
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# Google Vision OCR
def ocr_with_google_vision(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = {
        "requests": [{
            "image": {"content": img_base64},
            "features": [{"type": "TEXT_DETECTION"}],
            "imageContext": {"languageHints": ["ja"]}
        }]
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        annotations = response.json()["responses"][0].get("textAnnotations")
        return annotations[0]["description"] if annotations else ""
    else:
        return f"[Error] {response.status_code}: {response.text}"

# DeepL翻訳
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
    return response.json()["translations"][0]["text"] if response.status_code == 200 else f"[Error] {response.status_code}: {response.text}"

# 円価格→ドル換算（1ドル = 150円想定）
def convert_yen_to_usd(text, rate=150):
    match = re.search(r'¥?([0-9,]+)', text)
    if match:
        yen = int(match.group(1).replace(',', ''))
        usd = yen / rate
        return f"${usd:.2f}"
    return ""

# UI 設定
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        body {
            background: linear-gradient(145deg, #001f3f, #1a1a2e);
            color: white;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .block-container { padding-top: 2rem; }
        .stTextArea textarea { background-color: #1a1a2e; color: #fff; }
        .stButton>button {
            background-color: #003366; color: white; border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color:white;'>🍽️ メニュー翻訳アプリ（日本語→英語）</h2>", unsafe_allow_html=True)
st.write("画像をアップロードすると、料理名を英語に翻訳します。")

# ファイルアップロード
uploaded_file = st.file_uploader("📸 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", width=400)

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 翻訳結果（料理名 & 金額）")
        for line in lines:
            # 為替換算（日本円 → USD）
            usd_price = convert_yen_to_usd(line)
            with st.container():
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(
                        f"<div style='font-size:18px; padding:10px; background-color:#002244; border-radius:8px;'><strong>{line}</strong></div>",
                        unsafe_allow_html=True)
                with col2:
                    translated = translate_text_deepl(line)
                    display_text = f"➡️ <span style='color:#FFD700'>{translated}</span>"
                    if usd_price:
                        display_text += f" <span style='color:#aaa'>(approx. {usd_price})</span>"
                    st.markdown(
                        f"<div style='font-size:18px; padding:10px; background-color:#004466; border-radius:8px;'>{display_text}</div>",
                        unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")  