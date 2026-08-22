from .BaseController import BaseController
from models.db_schemes.minirag.schemes import Project, DataChunk
from stores.LLM.LLMEnums import DocumentTypeEnum
import asyncio
from cohere.errors import TooManyRequestsError
from openai import RateLimitError
from typing import List
import logging

logger = logging.getLogger(__name__)

class NLPController(BaseController):
     def __init__(self,vectordb_client, generation_client,embedding_client, template_parser):
          super().__init__()
          self.vectordb_client = vectordb_client  # Note: VectorDBProvider functions are async so we need to await them when calling them.
          self.embedding_client = embedding_client
          self.generation_client = generation_client
          self.template_parser = template_parser

     def create_collection_name(self, project_id):
          return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()

     async def reset_vector_db_collection(self, project: Project):
          # Bug: this used `Project.project_id` (the class), which has no runtime value.
          # Fix: read `project.project_id` from the actual project instance passed in.
          collection_name = self.create_collection_name(project_id=project.project_id)
          return await self.vectordb_client.delete_collection(collection_name= collection_name)

     async def get_vector_db_collection_info(self, project: Project):
          # Same class-vs-instance bug here: the collection name must come from the loaded project record.
          collection_name = self.create_collection_name(project_id=project.project_id)
          collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name)
          return collection_info

     async def index_into_vector_db(
     self,
     project: Project,
     chunks: List[DataChunk],
     chunks_ids: List[int],
     ):
          collection_name = self.create_collection_name(
               project_id=project.project_id
          )

          texts = [c.chunk_text for c in chunks]
          metadata = [c.chunk_metadata for c in chunks]

          vectors = None
          max_attempts = 5

          for attempt in range(1, max_attempts + 1):
               try:
                    vectors = self.embedding_client.embed_text(
                         text=texts,
                         document_type=DocumentTypeEnum.DOCUMENT.value,
                    )
                    break

               except (
                    TooManyRequestsError,
                    RateLimitError,
                    ) as error:
                    if attempt == max_attempts:
                         logger.exception(
                              "Embedding rate limit persisted "
                              "after %d attempts",
                              max_attempts,
                         )
                         raise

                    if isinstance(error, TooManyRequestsError):
                         retry_delay = 65
                    else:
                         retry_delay = min(
                              60,
                              5 * (2 ** (attempt - 1)),
                         )

                    logger.warning(
                         "Embedding rate limit reached. "
                         "Waiting %d seconds before retry %d/%d",
                         retry_delay,
                         attempt + 1,
                         max_attempts,
                    )

                    await asyncio.sleep(retry_delay)

          if not vectors or len(vectors) != len(texts):
               logger.error(
                    "Embedding count mismatch: expected %d vectors",
                    len(texts),
               )
               return False

          return await self.vectordb_client.insert_many(
               collection_name=collection_name,
               texts=texts,
               vectors=vectors,
               metadata=metadata,
               recored_ids=chunks_ids,
          )
     async def search_vector_db_collection(self, project: Project, text: str, limit: int=10):
          query_vector = None
          collection_name = self.create_collection_name(project_id=project.project_id)
          vectors = self.embedding_client.embed_text(text = text,
                                             document_type = DocumentTypeEnum.QUERY.value)

          if not vectors or len(vectors) == 0 :
               return False

          if isinstance(vectors, list) or len(vectors) > 0:
               query_vector = vectors[0]

          if not query_vector:
               logger.error("Failed to get query vector")
               return False

          results = await self.vectordb_client.search_by_vector(
               collection_name = collection_name,
               vector = query_vector,
               limit = limit
          )
          if not results:
               return

          return [
               result.model_dump()
               for result in results
          ]


     async def answer_rag_question(self, project: Project, query: str, limit: int = 10):
          # step1: retrieve related documents
          retieved_documents = await self.search_vector_db_collection(project=project, text=query, limit=limit)

          # Bug: returning None here caused a TypeError when the route tried to unpack
          # the result as (answer, full_prompt, chat_history).
          # Fix: always return a consistent tuple so the route can handle it cleanly.
          if not retieved_documents or len(retieved_documents) == 0:
               logger.warning("No documents retrieved from vector DB for query: '%s'", query)
               return None, None, None, []

          logger.info("Retrieved %d documents from vector DB.", len(retieved_documents))
          sources = self.build_sources(retieved_documents)

          # step2: construct LLM prompt
          system_prompt = self.template_parser.get("rag", "system_prompt")
          print(retieved_documents)

          documents_prompts = "\n".join([
               self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx,
                    "chunk_text": self.generation_client.process_text(doc["text"])
               })
               for idx, doc in enumerate(retieved_documents)
          ])

          footer_prompt = self.template_parser.get("rag", "footer_template", {
               "query": query
          })

          chat_history = [
               self.generation_client.construct_prompt(
                    prompt=system_prompt,
                    role=self.generation_client.enums.SYSTEM
               )
          ]

          full_prompt = "\n\n".join([documents_prompts, footer_prompt])

          logger.info("Sending prompt to LLM (length: %d chars).", len(full_prompt))

          answer = self.generation_client.generate_text(
               prompt=full_prompt,
               chat_history=chat_history
          )

          if not answer:
               logger.error("LLM returned no answer. Check that Ollama is running on port 11434.")

          return answer, full_prompt, chat_history, sources
     def build_sources(self, retrieved_documents):
          sources = []
          seen = set()

          for document in retrieved_documents:
               metadata = document.get("metadata") or {}
               file_id = metadata.get("file_id")
               page_number = metadata.get("page_number")

               if not file_id:
                    continue

               source_key = (file_id, page_number)

               if source_key in seen:
                    continue

               seen.add(source_key)

               sources.append({
                    "title": file_id,
                    "page_number": page_number,
                    "chunk_id": document.get("chunk_id"),
                    "score": document.get("score"),
               })

          return sources
