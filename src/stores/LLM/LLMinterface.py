from abc import ABC , abstractmethod

class LLMInterface(ABC):
     
    @abstractmethod  # to force used this method 
    def set_generation_model(self, model_id: str):
        pass

    @abstractmethod 
    def set_embedding_model(self, model_id: str, embeddig_size:int):
        pass

    @abstractmethod  
    def generate_text(self, prompt: str, max_output_token: int,
                      temperature: float = None):
        pass
     
    @abstractmethod
    def embed_text(self, text: str, document_type: str ):
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str): # call to handle prompt before generate text method usedit 
        pass