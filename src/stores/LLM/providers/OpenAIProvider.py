from ..LLMInterface import LLMInterface
from openai import OpenAI
import logging

class OpenAIProvider(LLMInterface):

     def __init__(self, api_key: str, api_url: str=None,
                  default_input_max_characters: int=1000,
                  default_generation_max_output_tokens: int=1000,
                  default_generation_tempreature: float=0.1):
          self.api_key = api_key
          self.api_url = api_url
          self.default_input_max_characters = default_input_max_characters
          self.default_generation_max_output_tokens = default_generation_max_output_tokens
          self.default_generation_tempreature = default_generation_tempreature

          self.generation_moddel_id = None

          self.embedding_model_id = None
          self.embedding_size = None

          self.client = OpenAI(
               api_key = self.api_key,
               api_url = self.api_url
          )

          self.logger = logging.getLogger(__name__)

     def set_generation_model(self, model_id: str):
          self.generation_moddel_id = model_id

     def set_embedding_model(self, model_id: str, embedding_size: int):  
          self.embedding_model_id = model_id   
          self.embedding_size = embedding_size

     def generate_text(self, prompt: str, max_output_token: int = None,
                      temperature: float = None):
          if not self.client :
               self.logger.error("client was not set!")
               return None
          
          if not self.generation_moddel_id : 
               self.logger.error("embedding model was not set")
               return None
          max_output_token = max_output_token if max_output_token else self.default_generation_max_output_tokens
          temperature = temperature if temperature else self.default_generation_tempreature

     def embed_text(self, text, document_type):
          if not self.client :
               self.logger.error("client was not set!")
               return None
          if not self.embedding_model_id: 
               self.logger.error("embedding model was not set")

          response = self.client.embeddings.create(
               model = self.embedding_model_id,
               input = text
          )
          # response validation 
          if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:       
               self.logger.error("Error while embedding text with OpenAI")
               return None 
          
          return response.data[0].embedding

     