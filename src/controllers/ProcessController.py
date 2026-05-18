from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import ProcessingEnum
from typing import List
from dataclasses import dataclass

@dataclass
class Documents: 
    page_content: str
    metadata: dict


class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id = project_id)

    def get_file_extention(self, file_id:str): # file_id => file name
       return os.path.splitext(file_id)[-1]

    def get_file_loader(self,file_id:str):
        file_ext = self.get_file_extention(file_id = file_id)
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


    def process_file_content(self, file_content: list, file_id:str,
                            chunk_size: int = 100 , overlap_size: int=20):
        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]
        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]
        chunks = self.prosecc_simpler_splitter(
            texts = file_content_texts,
            metadatas=file_content_metadata,
            chunk_size=chunk_size
            )

        return chunks
    def prosecc_simpler_splitter(self, texts: List[str], metadatas: List[dict], chunk_size: int, splitter_tag : str="\n"):
        full_text= " ".join(texts)

        lines = [ doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip())> 1]
        chunks = []
        current_chunk = ""
        for line in lines:
            current_chunk += splitter_tag + line
            if len(current_chunk) >= chunk_size:
                chunks.append(Documents(
                    page_content=current_chunk.strip(),
                    metadata={}
                ))
                current_chunk = ""
        
        if len(current_chunk) > 0:
            chunks.append(Documents(
                page_content=current_chunk.strip(),
                metadata={}
            ))
        return chunks