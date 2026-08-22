import asyncio
import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from tqdm.auto import tqdm

from controllers import NLPController
from models import ResponseSignal
from models.ChunkModel import ChunkModel
from models.ProjectModel import ProjectModel
from routes.schemes.nlp import PushRequest, SearchRequest


logger = logging.getLogger("uvicorn.error")

INDEX_BATCH_SIZE = 50
INDEX_BATCH_DELAY_SECONDS = 10


nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(
    request: Request,
    project_id: int,
    push_request: PushRequest,
):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            },
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        template_parser=request.app.template_parser,
    )

    collection_name = nlp_controller.create_collection_name(
        project_id=project.project_id
    )

    await request.app.vectordb_client.create_collection(
        collection_name=collection_name,
        embedding_size=request.app.embedding_client.embedding_size,
        do_reset=push_request.do_reset,
    )

    total_chunks_count = await chunk_model.get_chunk_count(
        project_id=project.project_id
    )

    page_no = 1
    inserted_item_count = 0

    pbar = tqdm(
        total=total_chunks_count,
        desc="Vector Indexing",
        position=0,
    )

    try:
        while True:
            page_chunks = await chunk_model.get_poject_chunks(
                project_id=project.project_id,
                page_no=page_no,
                page_size=INDEX_BATCH_SIZE,
            )

            if not page_chunks:
                break

            chunks_ids = [
                chunk.chunk_id
                for chunk in page_chunks
            ]

            is_inserted = await nlp_controller.index_into_vector_db(
                project=project,
                chunks=page_chunks,
                chunks_ids=chunks_ids,
            )

            if not is_inserted:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal":
                            ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value
                    },
                )

            inserted_item_count += len(page_chunks)
            page_no += 1
            pbar.update(len(page_chunks))

            logger.info(
                "Indexed %d/%d chunks for project %d",
                inserted_item_count,
                total_chunks_count,
                project.project_id,
            )

            if inserted_item_count < total_chunks_count:
                await asyncio.sleep(INDEX_BATCH_DELAY_SECONDS)

    finally:
        pbar.close()

    return JSONResponse(
        content={
            "signal":
                ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inseerted_item_count": inserted_item_count,
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(
    request: Request,
    project_id: int,
):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            },
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    collection_info = (
        await nlp_controller.get_vector_db_collection_info(
            project=project
        )
    )

    return JSONResponse(
        content={
            "signal":
                ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info["table_info"],
            "record_count": collection_info["record_count"],
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request,
    project_id: int,
    search_request: SearchRequest,
):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            },
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    results = await nlp_controller.search_vector_db_collection(
        project=project,
        text=search_request.text,
        limit=search_request.limit,
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value
            },
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "RESULTS": results,
        }
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_index(
    request: Request,
    project_id: int,
    search_request: SearchRequest,
):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            },
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    answer, full_prompt, chat_history, sources = (
        await nlp_controller.answer_rag_question(
            project=project,
            query=search_request.text,
            limit=search_request.limit,
        )
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.RAG_ANSWER_ERROR.value
            },
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "sources": sources,
            "full_prompt": full_prompt,
            "chat_history": chat_history,
        }
    )