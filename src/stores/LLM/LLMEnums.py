from enum import Enum

class LLMEnums(Enum):
     OPENAI = "OPENAI"
     COHERE = "COHERE"

class OpenAIEnums:
     SYSTEM = "system"
     USER = "user"
     ASSISTANT = "assistant"


class CohereEnums:
     SYSTEM = "SYSTEM"
     USER = "USER"
     ASSISTANT = "CHATBOT"
     DOCUMENT  = "search_ducoment"
     QUERY  = "search_query"
class DocumentTypeEnum(Enum):
     DOCUMENT = "document"
     QUEERY = "query"