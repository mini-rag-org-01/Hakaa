from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnum

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
        text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap_size,
        length_function=len,
        )
        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]
        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]

        chunks = text_splitter.create_documents(
            file_content_texts,
            metadatas = file_content_metadata
        )

        return chunks
