from enum import Enum

class LLMEnums(Enum):
     OPENAI = "OPENAI"
     COHERE = "COHERE"
     NEMOTRON = "NEMOTRON"

class OpenAIEnums:
     SYSTEM = "system"
     USER = "user"
     ASSISTANT = "assistant"


class CohereEnums:
     SYSTEM = "SYSTEM"
     USER = "USER"
     ASSISTANT = "CHATBOT"
     DOCUMENT  = "search_document"
     QUERY  = "search_query"

class DocumentTypeEnum(Enum):
     DOCUMENT = "document"
     QUERY = "query"
