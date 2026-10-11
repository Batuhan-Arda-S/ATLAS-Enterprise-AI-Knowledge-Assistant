from io import BytesIO

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.exceptions.file_upload import FileTooLargeError
from app.services.file_upload import MAX_EXTRACTED_TEXT_CHARS, MAX_PDF_PAGES

class DocumentParser:

    def extract_text(self,contents:bytes,content_type:str)->str:

        if content_type=="application/pdf":
            return self.extract_pdf_text(contents)

        if content_type=="text/plain":
            return self.extract_txt_text(contents)

        if content_type==("application/vnd.openxmlformats-officedocument."
                          "wordprocessingml.document"):

            return self.extract_docx_text(contents)

        raise ValueError("Unsupported content type")



    def extract_pdf_text(self, contents: bytes) -> str:

        pdf_stream = BytesIO(contents)
        reader=PdfReader(pdf_stream)
        if len(reader.pages) > MAX_PDF_PAGES:
            raise FileTooLargeError()

        page_texts=[]
        length = 0

        for page in reader.pages:
            text = page.extract_text()

            if text:
                length += len(text)
                if length > MAX_EXTRACTED_TEXT_CHARS:
                    raise FileTooLargeError()
                page_texts.append(text)

        return "\n".join(page_texts)

    def extract_txt_text(self,contents:bytes)->str:
        text = contents.decode("utf-8")
        if len(text) > MAX_EXTRACTED_TEXT_CHARS:
            raise FileTooLargeError()
        return text

    def extract_docx_text(self,contents:bytes)->str:

        docx_stream = BytesIO(contents)
        document=DocxDocument(docx_stream)

        paragraph_texts= []
        length = 0

        for paragraph in document.paragraphs:
            text=paragraph.text.strip()

            if text:
                length += len(text)
                if length > MAX_EXTRACTED_TEXT_CHARS:
                    raise FileTooLargeError()
                paragraph_texts.append(text)

        return "\n".join(paragraph_texts)



document_parser=DocumentParser()
