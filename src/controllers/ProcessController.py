import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import ProcessingEnum
from dataclasses import dataclass
import os

@dataclass
class Documents:
    page_content: str
    metadata: dict


class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id = project_id)

    def get_file_extension(self, file_id:str): # file_id => file name
       return os.path.splitext(file_id)[-1].lower()

    def get_file_loader(self,file_id:str):
        file_ext = self.get_file_extension(file_id = file_id)
        file_path = os.path.join(
            self.project_path ,
            file_id
        )
        # Bug: processing used to blow up with a deep loader traceback when the file id
        # did not exist under the given project folder.
        # Fix: return `None` early so the route can handle the missing file more clearly.
        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding = "utf-8")


        elif file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)

        return None


    def get_file_content(self, file_id: str):
        file_path = os.path.join(self.project_path, file_id)
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        loader = self.get_file_loader(file_id=file_id)
        if loader is None:
            # Bug: unsupported extensions used to fail later in less obvious ways.
            # Fix: raise a direct validation error at the controller boundary.
            raise ValueError(f"Unsupported file type for file_id: {file_id}")

        return loader.load()


    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\u00a0", " ")
        text = text.replace("\u200e", "")
        text = text.replace("\u200f", "")

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()


    def process_file_content(
        self,
        file_content: list,
        file_id: str,
        chunk_size: int = 400,
        overlap_size: int = 60,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap_size < 0:
            raise ValueError("overlap_size cannot be negative")

        if overlap_size >= chunk_size:
            raise ValueError(
                "overlap_size must be smaller than chunk_size"
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
            keep_separator="end",
            strip_whitespace=True,
            separators=[
                "\n\n",
                "\n",
                "؟",
                ".",
                "،",
                " ",
                "",
            ],
        )

        chunks = []

        for page_index, record in enumerate(file_content):
            page_text = self.clean_text(record.page_content)

            if not page_text:
                continue

            metadata = dict(record.metadata or {})
            metadata["file_id"] = file_id

            loader_page = metadata.get("page")

            if isinstance(loader_page, int):
                metadata["page_number"] = loader_page + 1
            else:
                metadata["page_number"] = page_index + 1

            page_chunks = splitter.create_documents(
                texts=[page_text],
                metadatas=[metadata],
            )

            for page_chunk_index, chunk in enumerate(page_chunks):
                chunk_metadata = dict(chunk.metadata)
                chunk_metadata["page_chunk_index"] = (
                    page_chunk_index + 1
                )

                chunks.append(
                    Documents(
                        page_content=chunk.page_content.strip(),
                        metadata=chunk_metadata,
                    )
                )

        return chunks
