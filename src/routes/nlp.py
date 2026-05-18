from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest,SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal 
import logging
from tqdm.auto import tqdm

logger = logging.getLogger("uvicorn.error")#route logger

nlp_router = APIRouter(
     prefix="/api/v1/nlp",
     tags = ["api_v1","nlp"],
)

@nlp_router.post("/index/push/{project_id}")

async def index_project(request: Request,project_id: int, push_request: PushRequest):
     project_model = await ProjectModel.create_instance(
          db_client =request.app.db_client  )
     
     chunk_model = await ChunkModel.create_instance(
          db_client= request.app.db_client
     )
     # Bug: without `await`, `project` was a coroutine, so `project.project_id` crashed later.
     # Fix: await the async DB call and store the real Project object.
     project = await project_model.get_project_or_create_one(project_id=project_id)

     if not project:
          return JSONResponse(
               status_code=status.HTTP_400_BAD_REQUEST,
                        # Bug: `JSONResponse` expects `content`, not `contents`.
                        # Fix: use the correct keyword so the error response is actually built.
                        content={ "signal" :ResponseSignal.PROJECT_NOT_FOUND_ERROR.value }
                                  )

     nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                    embedding_client=request.app.embedding_client,
                                    generation_client=request.app.generation_client,
                                    template_parser=request.app.template_parser,
                                    )
     
     has_records = True
     page_no = 1
     inseerted_item_count = 0
     idx = 0
     is_indexed_status = True

     collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
     
     _= await request.app.vectordb_client.create_collection(
          collection_name = collection_name,
          embedding_size = request.app.embedding_client.embedding_size,
          do_reset = push_request.do_reset
     )

     # setup batching
     total_chunks_count = await chunk_model.get_chunk_count(project_id=project.project_id)
     pbar = tqdm(total=total_chunks_count, desc='Vector Indexing', position=0)


     while has_records and is_indexed_status:
          page_chunks = await chunk_model.get_poject_chunks(project_id=project.project_id, page_no=page_no)
          if not page_chunks or len(page_chunks) == 0:
               has_records = False
               break
          page_no += 1
          chunks_ids = [c.chunk_id for c in page_chunks]
          idx += len(page_chunks) 

          is_inserted = await nlp_controller.index_into_vector_db(project=project,
                                                  chunks=page_chunks,
                                                  chunks_ids= chunks_ids)
          if not is_inserted:
               return JSONResponse(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    content={ "signal" :ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value }
               )
          pbar.update(len(page_chunks))
          inseerted_item_count += len(page_chunks)

     # return after the loop to report the total inserted chunk count.
     return JSONResponse(
          content={ "signal" :ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
                     "inseerted_item_count" : inseerted_item_count }
     )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
     project_model = await ProjectModel.create_instance(
          db_client=request.app.db_client
     )

     project = await project_model.get_project_or_create_one(project_id=project_id)

     nlp_controller = NLPController(
          vectordb_client= request.app.vectordb_client,
          generation_client= request.app.generation_client,
          embedding_client= request.app.embedding_client,
          template_parser = request.app.template_parser
     )

     collection_info = await nlp_controller.get_vector_db_collection_info(project=project)

     return JSONResponse(
          content={ "signal" :ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
                    "collection_info" : collection_info['table_info'],
                    "record_count" : collection_info['record_count'] }
     )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request,project_id: int, search_request: SearchRequest):

     project_model = await ProjectModel.create_instance(
          db_client =request.app.db_client  )
     project = await project_model.get_project_or_create_one(project_id=project_id)

     nlp_controller = NLPController(
          vectordb_client= request.app.vectordb_client,
          generation_client= request.app.generation_client,
          embedding_client= request.app.embedding_client,
          template_parser = request.app.template_parser
     )
     results = await nlp_controller.search_vector_db_collection(
          project=project,text = search_request.text, limit=search_request.limit)
     
     if not results :
          return JSONResponse(
               content={ "signal" :ResponseSignal.VECTORDB_SEARCH_ERROR.value})
     
     return JSONResponse(
          content={ "signal" :ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
                    "RESULTS" : results  }
     )


@nlp_router.post("/index/answer/{project_id}")
async def search_index(request: Request,project_id: int, search_request: SearchRequest):

     project_model = await ProjectModel.create_instance(
          db_client =request.app.db_client  )
     project = await project_model.get_project_or_create_one(project_id=project_id)

     nlp_controller = NLPController(
          vectordb_client= request.app.vectordb_client,
          generation_client= request.app.generation_client,
          embedding_client= request.app.embedding_client,
          template_parser = request.app.template_parser
     )
     answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
          project=project,
          query=search_request.text,
          limit=search_request.limit)
     
     if not answer :
          return JSONResponse(
               status_code =status.HTTP_400_BAD_REQUEST,
               content={ "signal" :ResponseSignal.RAG_ANSWER_ERROR.value})
     
     return JSONResponse(
          content={ "signal" :ResponseSignal.RAG_ANSWER_SUCCESS.value,
                    "answer" : answer,
                    "full_prompt": full_prompt,
                    "chat_history" : chat_history  }
     )
