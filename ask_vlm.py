import os
import base64
import json
import configparser
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
from openai import OpenAI
from prompt_version import prompt_vessel_diagram

# === Load Config ===
config = configparser.ConfigParser()
config.read("config.ini")

LOG_FILE = config["DEFAULT"]["LOG_FILE"]
IMAGE_OUTPUT_FOLDER = config["DEFAULT"].get("IMAGE_DIR", "images")
DPI = int(config["DEFAULT"].get("DPI", 300))
SHARPEN = float(config["DEFAULT"].get("SHARPEN", 1.5))
CONTRAST = float(config["DEFAULT"].get("CONTRAST", 1.5))

SYSTEM_PROMPT = prompt_vessel_diagram['prompt']


# === PDF to Image Conversion ===
def convert_pdf_to_images(pdf, output_folder, page_number, dpi=300, sharpen_factor=2.0, contrast_factor=2.0):
    page = pdf.load_page(page_number-1)
    pix = page.get_pixmap(dpi=dpi)
    raw_image_path = os.path.join(output_folder, f'raw_page_{page_number}.png')
    pix.save(raw_image_path)

    # Enhance image
    img = Image.open(raw_image_path)
    enhanced = ImageEnhance.Sharpness(img).enhance(sharpen_factor)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast_factor)
    final_path = os.path.join(output_folder, f'page_{page_number}.png')
    enhanced.save(final_path)
    os.remove(raw_image_path)

    return final_path


# === Encode file to base64 ===
def encode_file_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# === Extract specific page from PDF, optionally convert to image ===
def extract_page_from_pdf(original_pdf_path, output_folder, page_number, convert_to_image=False):

    os.makedirs(output_folder,exist_ok=True)

    
    doc = fitz.open(original_pdf_path)

    if page_number < 0 or page_number > len(doc):
        raise ValueError(f"Page number {page_number} is out of range for PDF with {len(doc)} pages.")
    
    if convert_to_image:
        output_path = convert_pdf_to_images(doc, output_folder, page_number, dpi=300, sharpen_factor=2.0, contrast_factor=2.0)
    else:
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_number-1, to_page=page_number-1)
        output_path = os.path.join(output_folder, f'page_{page_number}.pdf')
        new_doc.save(output_path)
        new_doc.close()
        doc.close()

    return output_path


# === Logging ===
def log_interaction(model, query, system_prompt, response):
    log_entry = {
        "model": model,
        "query": query,
        "system_prompt": system_prompt.strip(),
        "response": response.strip()
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def query_vlm_openai(query, input_path, is_image=False):
    api_key = config["OPENAI"]["API_KEY"]
    model = config["OPENAI"]["MODEL"]

    client = OpenAI(api_key=api_key)

    if is_image:
        # Read image as base64 and send as image_url
        with open(input_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")
        image_payload = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64_image}"
            }
        }
    else:
        # Assume PDF and use file upload method
        with open(input_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        image_payload = {
            "type": "file",
            "file": {
                "file_data": f"data:application/pdf;base64,{base64_pdf}",
                "filename": os.path.basename(input_path)
            }
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                image_payload
            ]
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )
    content = response.choices[0].message.content
    log_interaction(model, query, SYSTEM_PROMPT, content)
    return content

################################################3
import base64
from PIL import Image
import io
input_path=output_folder
output_dir = r'D:\chatbot project\P&ID\final_vlm_data_extraction\output'
os.makedirs(output_dir, exist_ok=True)
def encode_image(image_path):
    # Load and convert to JPEG
    pil_image = Image.open(input_path).convert('RGB')
    buffer = io.BytesIO()
    pil_image.save(buffer, format='JPEG', quality=95)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"  # Required prefix



def query_vlm_openai(query, input_path, is_image=False):
    api_key = config["OPENAI"]["API_KEY"]
    model = config["OPENAI"]["MODEL"]
    client = OpenAI(api_key=api_key)

    if is_image:
        # Convert PNG to JPEG, raw base64 (no data: prefix in url)
        from PIL import Image
        import io
        pil_img = Image.open(input_path).convert('RGB')
        buffer = io.BytesIO()
        pil_img.save(buffer, format='JPEG', quality=95)
        b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        image_payload = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
        }
    else:  # PDF
        # PDF as base64 (gpt-4o supports up to 20 pages)
        with open(input_path, "rb") as f:
            b64_pdf = base64.b64encode(f.read()).decode("utf-8")
        image_payload = {
            "type": "image_url",  # NOT "file"
            "image_url": {"url": f"data:application/pdf;base64,{b64_pdf}"}
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                image_payload
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",  # Ensure "gpt-4o" or "gpt-4-vision-preview"
        messages=messages,
        temperature=0
    )
    content = response.choices[0].message.content
    log_interaction(model, query, SYSTEM_PROMPT, content)
    return content


def query_vlm_openai(query, image_path=single_page_path, model="gpt-4o"):  # Force gpt-4o
    api_key = config["OPENAI"]["API_KEY"]
    client = OpenAI(api_key=api_key)

    # JPEG convert + correct base64
    from PIL import Image
    import io
    pil_img = Image.open(image_path).convert('RGB')
    buffer = io.BytesIO()
    pil_img.save(buffer, format='JPEG', quality=95)
    b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                }
            ]
        }
    ]

    response = client.chat.completions.create(
        model=model,  # "gpt-4o" only
        messages=messages,
        temperature=0
    )
    content = response.choices[0].message.content
    log_interaction(model, query, SYSTEM_PROMPT, content)
    return content

query="number of diagrams in the image"