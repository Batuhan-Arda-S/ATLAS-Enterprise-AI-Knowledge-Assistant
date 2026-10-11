from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile

from docx import Document as DocxDocument
from fastapi import UploadFile
from pypdf import PdfReader

from app.exceptions.file_upload import EmptyFileError,FileTooLargeError,UnsupportedFileTypeError


MAX_FILE_SIZE=10*1024*1024
MAX_EXTRACTED_TEXT_CHARS = 200_000
MAX_DOCX_UNCOMPRESSED_SIZE = 20*1024*1024
MAX_DOCX_ENTRIES = 1000
MAX_PDF_PAGES = 100

CONTENT_TYPE_EXTENSIONS={
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

class FileUploadService:

    async def validate_and_read(self,file:UploadFile)->bytes:

        filename = (file.filename or "").replace("\\", "/").split("/")[-1]
        if file.content_type not in CONTENT_TYPE_EXTENSIONS or (
            not filename or PurePosixPath(filename).suffix.lower() != CONTENT_TYPE_EXTENSIONS[file.content_type]
        ):
            raise UnsupportedFileTypeError()

        contents=await file.read(MAX_FILE_SIZE + 1)

        if len(contents)==0:
            raise EmptyFileError()

        if len(contents)>MAX_FILE_SIZE:
            raise FileTooLargeError()

        if file.content_type == "text/plain":
            try:
                text = contents.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise UnsupportedFileTypeError() from exc
            if "\x00" in text:
                raise UnsupportedFileTypeError()
            if len(text) > MAX_EXTRACTED_TEXT_CHARS:
                raise FileTooLargeError()
        elif file.content_type == "application/pdf":
            if not contents.startswith(b"%PDF-"):
                raise UnsupportedFileTypeError()
            try:
                reader = PdfReader(BytesIO(contents))
                if reader.is_encrypted:
                    raise UnsupportedFileTypeError()
                page_count = len(reader.pages)
            except Exception as exc:
                raise UnsupportedFileTypeError() from exc
            if page_count > MAX_PDF_PAGES:
                raise FileTooLargeError()
        else:
            try:
                with ZipFile(BytesIO(contents)) as archive:
                    entries = archive.infolist()
                    names = {entry.filename for entry in entries}
                    if not {"[Content_Types].xml", "word/document.xml"} <= names:
                        raise UnsupportedFileTypeError()
                    if len(entries) > MAX_DOCX_ENTRIES or sum(entry.file_size for entry in entries) > MAX_DOCX_UNCOMPRESSED_SIZE:
                        raise FileTooLargeError()
                    if any(entry.filename.startswith(("/", "\\")) or
                           ".." in entry.filename.replace("\\", "/").split("/") for entry in entries):
                        raise UnsupportedFileTypeError()
                    if archive.testzip() is not None:
                        raise UnsupportedFileTypeError()
                document = DocxDocument(BytesIO(contents))
                if sum(len(paragraph.text) for paragraph in document.paragraphs) > MAX_EXTRACTED_TEXT_CHARS:
                    raise FileTooLargeError()
            except (FileTooLargeError, UnsupportedFileTypeError):
                raise
            except Exception as exc:
                raise UnsupportedFileTypeError() from exc

        file.filename = filename
        return contents


file_upload_service = FileUploadService()
