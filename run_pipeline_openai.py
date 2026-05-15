import configparser
from ask_vlm import query_vlm_openai, extract_page_from_pdf

# === Load Config ===
config = configparser.ConfigParser()
config.read("config.ini")

pdf_path = config["DEFAULT"]["PDF_PATH"]
output_folder = config["DEFAULT"]["OUTPUT_FOLDER"]
PAGE_NUMBER = 4

# === Extract and Convert Page ===
single_page_path = extract_page_from_pdf(
    original_pdf_path=pdf_path,
    output_folder=output_folder,
    page_number=PAGE_NUMBER,
    convert_to_image=False 
)

# === Detect MIME type from file extension ===
is_image = single_page_path.lower().endswith((".png", ".jpg", ".jpeg"))

# === Query Loop ===
print("PDF page extracted. You can now query the OpenAI VLM.")
while True:
    query = input("\nEnter your query (or 'exit' to quit): ")
    if query.strip().lower() == "exit":
        break
    print("\n=== VLM Response ===\n")
    print(query_vlm_openai(query, single_page_path, is_image=is_image))
