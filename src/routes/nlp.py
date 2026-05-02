from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest,SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal 
import logging

logger = logging.getLogger("uvicorn.error")#route logger

nlp_router = APIRouter(
     prefix="/api/v1/nlp",
     tags = ["api_v1","nlp"],
)

@nlp_router.post("/index/push/{project_id}")

async def index_project(request: Request,project_id: str, push_request: PushRequest):
     project_model = await ProjectModel.create_instance(
          db_client =request.app.db_client  )
     
     chunk_model = await ChunkModel.create_instance(
          db_client= request.app.db_client
     )
     # Bug: without `await`, `project` was a coroutine, so `project.id` crashed later.
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
                                    )
     
     has_recorsd = True
     page_no = 1
     inseerted_item_count = 0
     idx = 0


     while has_recorsd:
          # Bug: this is an async model method; without `await` the code got a coroutine instead of chunk data.
          # Fix: await the paged chunk fetch and query by the Mongo project id stored in chunk records.
          
          page_chunks = await chunk_model.get_poject_chunks(project_id=project.id, page_no=page_no)
          if not page_chunks or len(page_chunks) == 0:
               has_recorsd = False
               break
          # Fix: advance the page only after a real page of chunks was returned.
          page_no += 1
          chunks_ids = list(range(idx, idx+len(page_chunks))) 
          idx += len(page_chunks)

          is_inserted = nlp_controller.index_into_vector_db(project=project,
                                                  chunks=page_chunks,
                                                  do_reset=push_request.do_reset,
                                                  chunks_ids= chunks_ids)
          if not is_inserted:
               return JSONResponse(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    # Bug: same wrong keyword here (`contents`).
                    # Fix: use `content` so FastAPI returns the JSON payload.
                    content={ "signal" :ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value }
               )
          
          inseerted_item_count += len(page_chunks)

     # Bug: the old code returned inside the loop, so only the first page was ever indexed.
     # Fix: return after the loop to report the total inserted chunk count.
     return JSONResponse(
          content={ "signal" :ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
                     "inseerted_item_count" : inseerted_item_count }
     )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
     project_model = await ProjectModel.create_instance(
          db_client=request.app.db_client
     )

     project = await project_model.get_project_or_create_one(project_id=project_id)

     nlp_controller = NLPController(
          vectordb_client= request.app.vectordb_client,
          generation_client= request.app.generation_client,
          embedding_client= request.app.embedding_client,
     )

     collection_info = nlp_controller.get_vector_db_collection_info(project=project)

     return JSONResponse(
          content={ "signal" :ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
                     "inseerted_item_count" : collection_info  }
     )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request,project_id: str, search_request: SearchRequest):

     project_model = await ProjectModel.create_instance(
          db_client =request.app.db_client  )
     project = await project_model.get_project_or_create_one(project_id=project_id)

     nlp_controller = NLPController(
          vectordb_client= request.app.vectordb_client,
          generation_client= request.app.generation_client,
          embedding_client= request.app.embedding_client,
     )
     results = nlp_controller.search_vector_db_collection(
          project=project,text = search_request.text, limit=search_request.limit)
     
     if not results :
          return JSONResponse(
               content={ "signal" :ResponseSignal.VECTORDB_SEARCH_ERROR.value})
     
     return JSONResponse(
          content={ "signal" :ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
                    "RESULTS" : results  }
     )