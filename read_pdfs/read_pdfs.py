import os
import re
from PyPDF2 import PdfReader
import concurrent.futures
from io import BytesIO
import fitz


def load_pdf_in_memory(pdf_path):
    with open(pdf_path, "rb") as f:
        return f.read()


# def search_sentence_in_pdf(pdf_path, sentence):
#     pattern = re.compile(re.escape(sentence), re.IGNORECASE)
#     found = False

#     reader = PdfReader(BytesIO(load_pdf_in_memory(pdf_path)))

#     for page in reader.pages:
#         text = page.extract_text()

#         if text and pattern.search(text):
#             found = True
#             break

#     return found

def search_sentence_in_pdf(pdf_path, sentence):

    pattern = re.compile(re.escape(sentence), re.IGNORECASE)
    found = False

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if text and pattern.search(text):
                found = True
                break

    return found


def get_pdf_files(folder_path):
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

pdfs_path = "/media/eavelar/860/MEGA/pdf books repo/"
# pdfs_path = "/home/eavelar/Documents/"
sentence = "ThreadPoolExecutor"

pdf_files = get_pdf_files(pdfs_path)

def process_pdf(pdf_path):
    file_name = os.path.basename(pdf_path)
    print(f"Searching in: {file_name}")
    found = search_sentence_in_pdf(pdf_path, sentence)
    if found:
        print(f"Found in: {file_name}")

max_workers = 20

with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    executor.map(process_pdf, pdf_files)