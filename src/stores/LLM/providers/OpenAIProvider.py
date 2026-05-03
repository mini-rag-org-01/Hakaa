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


          response = self.client.chat.completions.create(
               model = self.generation_moddel_id,
               messages = chat_history, 
               max_tokens = max_output_token,
               temperature = temperature
          )
          if not response or not response.choices or len(response.choices) == 0 or not response.choices[0]:
               self.logger.error("Error while text with openAI")
               return None
          # Bug: `choices` is a list, so `response.choices.message` raises
          # `AttributeError: 'list' object has no attribute 'message'`.
          # Fix: read the first choice, then access its message content.
          return response.choices[0].message.content

     def embed_text(self, text: str, document_type: str =None):
          # Fix: share one implementation for single and batched embedding calls.
          response = self.embed_texts([text], document_type=document_type)
          if not response or len(response) == 0:
               return None
          return response[0]

     def embed_texts(self, texts: list, document_type: str =None):
          if not self.client :
               self.logger.error("client was not set!")
               return None
          if not self.embedding_model_id: 
               self.logger.error("embedding model was not set")
               return None

          response = self.client.embeddings.create(
               model = self.embedding_model_id,
               # Bug: `text` does not exist in this batched method; the payload should be the
               # incoming `texts` list so OpenAI returns one embedding per input string.
               # Fix: pass `texts` to the embeddings API.
               input=texts
          )
          # response validation 
          if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
               self.logger.error("Error while embedding text with OpenAI")
               return None 
          
          # Fix: return all vectors so the controller can embed many chunks in one request.
          return [item.embedding for item in response.data]

     def construct_prompt(self, prompt: str, role: str):
          return {
               "role": role,
               "content": self.process_text(prompt)
          }
