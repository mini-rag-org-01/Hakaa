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
          self.default_max_input_characters = default_max_input_characters
          self.default_generation_max_output_tokens = default_generation_max_output_tokens
          self.default_generation_temprature = default_generation_temprature


          self.generation_moddel_id = None

          self.embedding_model_id = None
          self.embedding_size = None

          self.client = co.Client(api_key = self.api_key)
    

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

          if not self.client :
               self.logger.error("cohere client was not set!")
               return None
          
          if not self.embedding_model_id: 
               self.logger.error("embedding model was not set")

          input_type = CohereEnums.DOCUMENT
          if document_type == DocumentTypeEnum.QUEERY:
               input_type = CohereEnums.QUERY

          response = self.client.embed(
               model = self.embedding_model_id,
               texts = [self.process_text(text)],
               input_type = input_type,
               embedding_types=['float']
          )
          # response validation 
          if not response or not response.embeddings or response.embeddings.float :       
               self.logger.error("Error while embedding text with cohere")
               return None 
          
          return response.data[0].embedding

     def construct_prompt(self, prompt: str, role: str):
          return {
               "role": role,
               "content": self.process_text(prompt)
          }