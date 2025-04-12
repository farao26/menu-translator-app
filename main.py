import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

# Use Streamlit Secrets in production
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# Background styling with royal blue
def set_background(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode()
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .card {{
        background-color: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Set background image
set_background("pngtree-vector-royal-blue-abstract-background-image_303102.jpg")

# Google Cloud Vision OCR

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

# DeepL translation

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

# App UI
st.markdown("""
    <h1 style='text-align: center; color: white;'>🍷 Menu Translator</h1>
    <p style='text-align: center; color: #ddd;'>高級レストランのメニューをスマートに翻訳</p>
    <hr style='border-top: 1px solid #ccc;'>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("画像をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.subheader("🔍 OCR結果")
    text = ocr_with_google_vision(image)
    st.text_area("抽出された日本語テキスト", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌍 翻訳結果")
        for line in lines:
            st.markdown(f"<div class='card'><b>🍽️ 日本語:</b> {line}<br><b>➡️ 英語:</b> {translate_text_deepl(line)}</div>", unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")