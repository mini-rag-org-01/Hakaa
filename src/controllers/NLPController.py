from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.LLM.LLMEnums import DocumentTypeEnum
from typing import List

class NLPController(BaseController):
     def __init__(self,vectordb_client, generation_client,embedding_client):
          super().__init__()
          self.vectordb_client = vectordb_client
          self.embedding_client = embedding_client
          self.generation_client = generation_client

     def create_collection_name(self, project_id):
          return f"collection_{project_id}".strip() 
     
     def reset_vector_db_collection(self, project: Project): 
          # Bug: this used `Project.project_id` (the class), which has no runtime value.
          # Fix: read `project.project_id` from the actual project instance passed in.
          collection_name = self.create_collection_name(project_id=project.project_id)
          return self.vectordb_client.delete_collection(collection_name= collection_name)
     
     def get_vector_db_collection_info(self, project: Project):
          # Same class-vs-instance bug here: the collection name must come from the loaded project record.
          collection_name = self.create_collection_name(project_id=project.project_id)
          collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)
          return collection_info

     def index_into_vector_db(self, project:Project, chunks: List[DataChunk], 
                              chunks_ids : List[int], 
                              do_reset: bool = False):
          # Bug: using `Project.project_id` raised `AttributeError: project_id`.
          # Fix: derive the collection name from the current project instance.
          collection_name = self.create_collection_name(project_id=project.project_id)

          # 2. manage items 
          texts = [c.chunk_text for c in chunks]
          metadata = [c.chunk_metadata for c in chunks]
          # Bug: embedding one chunk per API call quickly hits Cohere's trial limit.
          # Fix: send the whole page of chunk texts in a single batched embed request.
          vectors = self.embedding_client.embed_texts(
               texts=texts,
               document_type=DocumentTypeEnum.DOCUMENT.value
          )
          if not vectors or len(vectors) != len(texts):
               return False

          # Bug: `vectordb_client.embedding_sizev` does not exist on the vector DB client.
          # Fix: the embedding size belongs to the embedding client that produced the vectors.
          _ = self.vectordb_client.create_collection(
               collection_name=collection_name,
               do_reset=do_reset,
               embedding_size=self.embedding_client.embedding_size

          )
          # Bug: the old code discarded the insert result, so the route could not tell whether insertion worked.
          # Fix: return the provider result to the caller.
          return self.vectordb_client.insert_many(
               collection_name=collection_name,
               texts=texts,
               vectors=vectors,
               metadata=metadata,
               record_ids = chunks_ids,
          )
     
     def search_vector_db_collection(self, project: Project, text: str, limit: int=10):
          collection_name = self.create_collection_name(project_id=project.project_id)

          vector = self.embedding_client.embed_text(text = text,
                                             document_type = DocumentTypeEnum.QUERY.value)
          
          if not vector or len(vector) == 0 :
               return False
          
          results = self.vectordb_client.search_by_vector(
               collection_name = collection_name,
               vector = vector,
               limit = limit 
          )
          
          if not results:
               return 
          
          return [
               result.dict()
               for result in results
          ]