from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI, APIConnectionError
import logging
from typing import Union, List

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
               base_url = self.api_url if self.api_url and len(self.api_url) else None

          )

          self.enums = OpenAIEnums
          self.logger = logging.getLogger(__name__)

     def set_generation_model(self, model_id: str):
          self.generation_moddel_id = model_id

     def set_embedding_model(self, model_id: str, embedding_size: int):  
          self.embedding_model_id = model_id   
          self.embedding_size = embedding_size


     def process_text(self, text: str):
          return text[:self.default_input_max_characters].strip()
     
     def generate_text(self, prompt: str,  chat_history: list=[],
                    max_output_token: int=None,temperature: float = None):
           
          if not self.client :
               self.logger.error("client was not set!")
               return None
          
          if not self.generation_moddel_id : 
               self.logger.error("embedding model was not set")
               return None
          
          max_output_token = max_output_token if max_output_token else self.default_generation_max_output_tokens
          temperature = temperature if temperature else self.default_generation_tempreature

          chat_history.append(
          self.construct_prompt(prompt=prompt, role=OpenAIEnums.USER))

          try:
               response = self.client.chat.completions.create(
                    model = self.generation_moddel_id,
                    messages = chat_history,
                    max_tokens = max_output_token,
                    temperature = temperature
               )
          except APIConnectionError as e:
               self.logger.error(
                    f"LLM connection error: could not reach '{self.api_url}'. "
                    f"Make sure Ollama (or your LLM server) is running. Details: {e}"
               )
               return None

          if not response or not response.choices or len(response.choices) == 0 or not response.choices[0]:
               self.logger.error("Error while generating text with OpenAI")
               return None

          return response.choices[0].message.content

     def embed_text(self, text: Union[str, List[str]], document_type: str =None):
          if not self.client :
               self.logger.error("OpenAI client was not set!")
               return None

          if isinstance(text, str):
               text = [text]
               
          if not self.embedding_model_id: 
               self.logger.error("embedding model for OpenAI was not set")
               return None

          try:
               response = self.client.embeddings.create(
                    model = self.embedding_model_id,
                    input=text
               )
          except APIConnectionError as e:
               self.logger.error(
                    f"LLM connection error: could not reach '{self.api_url}'. "
                    f"Make sure Ollama (or your LLM server) is running. Details: {e}"
               )
               return None

          # response validation
          if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
               self.logger.error("Error while embedding text with OpenAI")
               return None

          # Return all vectors so the controller can embed many chunks in one request.
          return [item.embedding for item in response.data]

     def construct_prompt(self, prompt: str, role: str):
          return {
               "role": role,
               "content": prompt
          }
