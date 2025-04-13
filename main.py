import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv

# --- Secrets から API キーを読み込み ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# --- Google Cloud Vision API を使った OCR 関数 ---
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

# --- DeepL 翻訳関数 ---
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

# --- 円記号をドル換算する関数（例：\864 → $5.70） ---
def convert_yen_to_usd(text, rate=0.0066):
    import re
    def replace_func(match):
        yen = int(match.group(1))
        usd = yen * rate
        return f"\u00a5{yen} (\u0024{usd:.2f})"
    return re.sub(r"\\(\\?)(\d{3,5})", replace_func, text)

# --- UI Styling ---
st.set_page_config(layout="wide")
st.markdown("""
<style>
body {
    background: linear-gradient(145deg, #001f3f, #1a1a2e);
    color: white;
    font-family: 'Helvetica Neue', sans-serif;
}
.block-container {
    padding-top: 2rem;
}
.stTextArea textarea {
    background-color: #1a1a2e;
    color: #fff;
}
.stButton>button {
    background-color: #003366;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- App UI ---
st.title("📸 Menu OCR & Translator - 高級レストラン風")
st.write("日本語メニューを画像から読み取り、英語へ翻訳し、円→ドル換算も表示します。")

uploaded_file = st.file_uploader("📸 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.markdown("---")
    st.subheader("🔍 OCRで抽出された日本語テキスト")
    text = ocr_with_google_vision(image)
    st.text_area("OCR結果", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌍 翻訳＆価格換算")
        for line in lines:
            col1, col2 = st.columns([1, 1])
            with col1:
                styled_line = convert_yen_to_usd(line)
                st.markdown(
                    f"<div style='font-size:20px; font-weight:bold; font-family:Georgia, serif; padding:10px; background-color:#002244; border-radius:8px;'>{styled_line}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                translated = translate_text_deepl(line)
                st.markdown(
                    f"<div style='font-size:18px; padding:10px; background-color:#004466; border-radius:8px;'>➡️ {translated}</div>",
                    unsafe_allow_html=True
                )
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")
        