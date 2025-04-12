import streamlit as st
from PIL import Image
import io
import base64
import requests
import json

# secrets からAPIキーを取得
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# --- CSS でオシャレに ---
st.markdown("""
    <style>
        .main-title {
            font-size: 3em;
            text-align: center;
            font-weight: bold;
            color: #4CAF50;
        }
        .subtitle {
            font-size: 1.5em;
            margin-top: 30px;
            color: #555;
        }
        .ocr-text, .translation-text {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- OCR関数（Google Cloud Vision） ---
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
        return annotations[0]["description"] if annotations else ""
    else:
        return f"[Error] {response.status_code}: {response.text}"

# --- 翻訳関数（DeepL） ---
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

# --- UI ---
st.markdown("<div class='main-title'>📸 Menu Translator</div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("画像をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロード画像", use_column_width=True)

    st.markdown("<div class='subtitle'>🔍 OCR結果（日本語）</div>", unsafe_allow_html=True)
    text = ocr_with_google_vision(image)
    st.markdown(f"<div class='ocr-text'>{text.replace('\n', '<br>')}</div>", unsafe_allow_html=True)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.markdown("<div class='subtitle'>🌍 DeepL 翻訳</div>", unsafe_allow_html=True)
        for line in lines:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"<div class='ocr-text'>🍽️ {line}</div>", unsafe_allow_html=True)
            with col2:
                translation = translate_text_deepl(line)
                st.markdown(f"<div class='translation-text'>➡️ {translation}</div>", unsafe_allow_html=True)
    else:
        st.warning("テキストが抽出できませんでした。画像を確認してください。")