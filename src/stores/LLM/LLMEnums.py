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
     # Bug: Cohere expects `search_document`; the old typo `search_ducoment`
     # made the API reject the request as an invalid input_type.
     DOCUMENT  = "search_document"
     QUERY  = "search_query"
class DocumentTypeEnum(Enum):
     DOCUMENT = "document"
     QUERY = "query"
