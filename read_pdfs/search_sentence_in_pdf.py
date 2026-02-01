def search_sentence_in_pdf(pdf_path, sentence):
    pattern = re.compile(re.escape(sentence), re.IGNORECASE)
    found = False

    reader = PdfReader(pdf_path)

    for page in reader.pages:
        text = page.extract_text()
        if text and pattern.search(text):
            found = True
            break

    return found