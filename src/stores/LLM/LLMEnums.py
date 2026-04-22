from enum import Enum

class LLMEnums(Enum):
     OPENAI = "OPENAI"
     COHERE = "COHERE"

class OpenAIEnums:
     SYSTEM = "system"
     USER = "user"
     ASSISTANT = "assistant"