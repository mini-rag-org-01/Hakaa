from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
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


     def process_text(self, text: str):
          return text[:self.default_input_max_characters].strip()
     
     def generate_text(self, prompt: str, max_output_token: int=None,
                    chat_history: list=[],temperature: float = None):
          
          if not self.client :
               self.logger.error("client was not set!")
               return None
          
          if not self.generation_moddel_id : 
               self.logger.error("embedding model was not set")
               return None
          max_output_token = max_output_token if max_output_token else self.default_generation_max_output_tokens
          temperature = temperature if temperature else self.default_generation_tempreature

          chat_history.append(
               self.construct_prompt(OpenAIEnums.USER.value)
          )
          response = self.client.chat.completions.create(
               model = self.generation_moddel_id,
               messages = chat_history, 
               max_tokens = max_output_token,
               temperature = temperature
          )
          if not response or not response.choices or len(response.choices) == 0 or not response.choices[0]:
               self.logger.error("Error while text with openAI")
               return None
          return response.choices.message["content"]

     def embed_text(self, text: str, document_type: str =None):
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

     def construct_prompt(self, prompt: str, role: str):
          return {
               "role": role,
               "content": self.process_text(prompt)
          }