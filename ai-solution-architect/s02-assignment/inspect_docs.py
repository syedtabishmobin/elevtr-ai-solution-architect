import glob
import os

from pypdf import PdfReader

search_term = "619,003"

for path in sorted(glob.glob("docs/*.pdf")):
    text = "\n".join(
        (page.extract_text() or "")
        for page in PdfReader(path).pages
    )

    if search_term.lower() in text.lower():
        print(path, "FOUND")