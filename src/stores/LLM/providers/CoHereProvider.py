from ..LLMInterface import LLMInterface
from ..LLMEnums import CohereEnums,DocumentTypeEnum
import cohere as co
import logging

class CoHereProvider(LLMInterface):

     def __init__(self, api_key: str,
                  default_max_input_characters: int=1000,
                  default_generation_max_output_tokens: int=1000,
                  default_generation_temprature: float=0.1):
          self.api_key = api_key
          # Bug: `process_text()` reads `self.default_input_max_characters`, so storing the
          # constructor value under `default_max_input_characters` caused `AttributeError`.
          # Fix: keep the attribute name aligned with the rest of the provider methods.
          self.default_input_max_characters = default_max_input_characters
          self.default_generation_max_output_tokens = default_generation_max_output_tokens
          self.default_generation_temprature = default_generation_temprature


          self.generation_moddel_id = None

          self.embedding_model_id = None
          self.embedding_size = None

          self.client = co.Client(api_key = self.api_key)
    
          self.enums = CohereEnums
          self.logger = logging.getLogger(__name__)

    
     def set_generation_model(self, model_id:str):
          self.generation_moddel_id = model_id

     def set_embedding_model(self, model_id: str, embedding_size: int):  
          self.embedding_model_id = model_id   
          self.embedding_size = embedding_size

     def process_text(self, text: str):
          return text[:self.default_input_max_characters].strip()
     
     def generate_text(self, prompt: str,  chat_history: list=[],
                    max_output_token: int=None,temperature: float = None):
          
          if not self.client :
               self.logger.error("CoHere client was not set!")
               return None
          
          if not self.generation_moddel_id : 
               self.logger.error("embedding model was not set")
               return None

          max_output_token = max_output_token if max_output_token else self.default_generation_max_output_tokens
          temperature = temperature if temperature else self.default_generation_tempreature
          
          response = self.client.chat(
               model = self.generation_moddel_id,
               chat_history = chat_history,
               messages = self.process_text(prompt),
               temperature = temperature,
               max_tokens = self.default_max_input_characters
          )
          if not response or not response.message or len(response.message) == 0 or not response.message.content[0] or not response.message.content[0].text:
               self.logger.error("Error while text with cohere")
               return None
          return response.message.content[0].text
     


     def embed_text(self, text: str, document_type: str =None):
          # Fix: keep the single-text API, but route it through the new batch method
          # so both code paths use the same validation and Cohere request format.
          response = self.embed_texts([text], document_type=document_type)
          if not response or len(response) == 0:
               return None
          return response[0]

     def embed_texts(self, texts: list, document_type: str =None):

          if not self.client :
               self.logger.error("cohere client was not set!")
               return None
          
          if not self.embedding_model_id: 
               self.logger.error("embedding model was not set")
               return None

          # Bug: the old code passed Enum members (for example `CohereEnums.DOCUMENT`)
          # instead of their string values, and the document enum value itself had a typo.
          # Cohere expects literal strings like `search_document` / `search_query`.
          # Fix: send the literal string constants from `CohereEnums`.
          input_type = CohereEnums.DOCUMENT
          if document_type == DocumentTypeEnum.QUERY.value:
               input_type = CohereEnums.QUERY

          # Fix: batch many chunks into one Cohere embed request to reduce API calls
          # and avoid hitting the trial key rate limit as quickly.
          response = self.client.embed(
               model = self.embedding_model_id,
               texts=[self.process_text(text) for text in texts],
               input_type = input_type,
               embedding_types=['float']
          )
          # response validation 
          # Bug: the old check treated a valid float embedding payload as an error because
          # `response.embeddings.float` is supposed to exist on success.
          # Fix: only fail when the float embeddings are missing or empty.
          if not response or not response.embeddings or not response.embeddings.float:
               self.logger.error("Error while embedding text with cohere")
               return None 
          
          # Fix: return the whole batch of embeddings so callers can map one vector per chunk.
          return response.embeddings.float

     def construct_prompt(self, prompt: str, role: str):
          return {
               "role": role,
               "content": prompt
          }
