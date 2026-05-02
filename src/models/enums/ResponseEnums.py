from enum import Enum


class ResponseSignal(Enum):

    FILE_VALIDATED_SUCCESS  = "file_validated_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOADED_SUCCESS = "file_uploaded_success"
    FILE_UPLOADED_FAILED  = "file_uploaded_failed"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    NO_FILES_ERROR = "not found files"
    FILE_ID_ERROR = "not file found with id"
    PROJECT_NOT_FOUND_ERROR = "project not found"
    INSERT_INTO_VECTORDB_ERROR = "iinsert into vectordb error "
    INSERT_INTO_VECTORDB_SUCCESS = "iinsert into vectordb success "
    VECTORDB_COLLECTION_RETRIEVED = "vector collection retrieved"
    VECTORDB_SEARCH_ERROR = "VECTORDB_SEARCH_ERROR"
    VECTORDB_SEARCH_SUCCESS = "VECTORDB_SEARCH_SUCCESS"