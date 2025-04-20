import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
import openai
from dotenv import load_dotenv

# --- 読み込み ---
load_dotenv()
GOOGLE_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

# --- OCR関数 ---
def ocr_google_vision(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    body = {
        "requests": [
            {
                "image": {"content": img_base64},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["ja"]}
            }
        ]
    }

    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(body))
    if response.status_code == 200:
        annotations = response.json()["responses"][0].get("textAnnotations")
        if annotations:
            return annotations[0]["description"]
        else:
            return ""
    else:
        return f"[Error] {response.status_code}: {response.text}"

# --- DeepL翻訳 ---
def translate_deepl(text):
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "JA",
        "target_lang": "EN"
    }
    response = requests.post(url, data=data)
    return response.json()["translations"][0]["text"] if response.status_code == 200 else "翻訳エラー"

# --- ChatGPTで料理説明取得 ---
def get_dish_analysis(dish_name):
    prompt = f"""料理名：「{dish_name}」\n1. 一般的に使われる材料（簡潔に）\n2. アレルギーの可能性のある食材\n3. 簡単な説明（50文字以内）\n4. 歴史や小話（50文字以内）"""
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- UI構成 ---
st.set_page_config(layout="wide", page_title="Menu Translator")
st.title("🍽️ 高級感のあるメニュー翻訳アプリ")
st.markdown("画像から日本語メニューを英語に翻訳し、さらに料理の解説も表示します。")

uploaded_file = st.file_uploader("メニュー画像をアップロード", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    text = ocr_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.markdown("---")
        st.subheader("翻訳と解説結果")
        for line in lines:
            translated = translate_deepl(line)
            with st.expander(f"🍴 {line} ➡️ {translated}"):
                st.markdown(f"**🔍 詳細解析：**")
                st.markdown(get_dish_analysis(line))
    else:
        st.warning("テキストが読み取れませんでした。画像を確認してください。")

           