import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
import google.generativeai as genai

# --- API Keys ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- Gemini Init ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# --- OCR ---
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
        return ""

# --- Translation ---
def translate_text_deepl(text, source_lang="JA", target_lang="EN"):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()["translations"][0]["text"] if response.status_code == 200 else ""

# --- Dish Check & Info (Gemini) ---
def get_dish_info_with_gemini(name_en):
    prompt = f"""
Is "{name_en}" a food dish? If it is, answer in the following format:

1. Common Ingredients (3–5)
2. Potential Allergens (start with "Generally includes...")
3. Short Description (within 50 characters)
4. History / Trivia (within 50 characters)

If not a food, just answer: "NOT_A_DISH"
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# --- UI Config ---
st.set_page_config(layout="wide", page_title="Elegant Menu Translator")
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to right, #1e3c72, #2a5298);
        color: white;
    }
    .stTextArea textarea {
        background-color: #1a1a2e; color: #fff;
    }
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- App UI ---
st.title("🍽️ Elegant Menu Translator (Gemini + DeepL)")
st.caption("Upload an image and get English translation + dish info.")

uploaded_file = st.file_uploader("📷 Upload Japanese menu image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded image", use_column_width=True)

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌐 Translated Dishes & Info")
        for line in lines:
            translated = translate_text_deepl(line)
            dish_info = get_dish_info_with_gemini(translated)

            if "NOT_A_DISH" in dish_info:
                continue  # Skip non-dish items

            with st.container():
                st.markdown(
                    f"""
                    <div style='padding:10px; border:1px solid #444; border-radius:10px; margin-bottom:15px; background-color:#222;'>
                        <b style='font-size:20px; color:#ffd700;' title="{dish_info.replace('"', '&quot;')}">{translated}</b>
                        <br>
                        <span style='color:#aaa; font-size:14px;'>{line}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("No text detected. Please try a clearer image.")
            