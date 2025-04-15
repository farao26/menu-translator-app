import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
import re

# --- Load secrets securely ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# --- OCR with Google Cloud Vision API ---
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

# --- DeepL translation ---
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

# --- Currency converter ---
def convert_yen_to_usd(text, rate=0.0068):
    def replacer(match):
        yen = int(match.group(1))
        usd = round(yen * rate, 2)
        return f"\u00a5{yen} (\u0024{usd})"

    return re.sub(r"\\u00a5?(\\d{3,5})", replacer, text)

# --- UI Layout ---
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #0f0f0f, #1c1c3c);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stTextArea textarea {
        background-color: #1c1c3c;
        color: white;
    }
    .translated-word {
        display: inline-block;
        background-color: #2a2a5a;
        border-radius: 12px;
        padding: 5px 10px;
        margin: 3px;
        font-size: 16px;
    }
    .translated-word a {
        color: #f4d03f;
        text-decoration: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🍽️ 高級レストラン風 メニュー翻訳アプリ")
st.caption("画像から日本語メニューを抽出し、英語翻訳と画像検索リンクを提供します。")

uploaded_file = st.file_uploader("📸 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)
    st.markdown("---")

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 翻訳結果 & 検索リンク")
        for line in lines:
            translated = translate_text_deepl(line)
            translated = convert_yen_to_usd(translated)

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"<div style='font-size:18px; padding:10px; background-color:#222; border-radius:8px;'><strong>{line}</strong></div>", unsafe_allow_html=True)
            with col2:
                words = translated.split()
                word_html = "".join([
                    f"<span class='translated-word'><a href='https://www.google.com/search?tbm=isch&q={word}' target='_blank'>{word}</a></span>"
                    for word in words
                ])
                st.markdown(word_html, unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")
