import streamlit as st
from PIL import Image
import pytesseract
import cv2
import numpy as np
import io
import requests
import os
from dotenv import load_dotenv

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

# .envファイルからAPIキーを読み込み
load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

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

# OCR前処理関数
def preprocess_image(img):
    img = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    return thresh

# Streamlit UI
st.title("📸 Menu OCR & Translator")
st.write("画像から日本語のテキストを抽出して英語に翻訳します。")

uploaded_file = st.file_uploader("画像をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.subheader("🔍 OCR処理中...")
    preprocessed = preprocess_image(image)
    text = pytesseract.image_to_string(preprocessed, lang='jpn', config='--oem 3 --psm 6')

    st.subheader("📝 抽出された日本語テキスト")
    st.text_area("OCR結果", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌍 DeepL 翻訳結果（左右に並べて表示）")
        for line in lines:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🍽️ {line}**")
            with col2:
                translation = translate_text_deepl(line)
                st.markdown(f"➡️ {translation}")
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")