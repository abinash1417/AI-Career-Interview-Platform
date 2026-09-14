from pypdf import PdfReader


class ResumeParser:
    """Extracts text content from an uploaded resume PDF."""

    @staticmethod
    def extract_text(file) -> str:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()