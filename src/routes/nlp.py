from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest
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
     project = project_model.get_project_or_create_one(project_id=project_id)

     if not project:
          return JSONResponse(
               status_code=status.HTTP_400_BAD_REQUEST,
                        contents ={ "signal" :ResponseSignal.PROJECT_NOT_FOUND_ERROR.value }
                                  )

     nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                    embedding_client=request.app.embedding_client,
                                    generation_client=request.app.generation_client,
                                    )
     
     has_recorsd = True
     page_no = 1
     inseerted_item_count = 0
     while has_recorsd:
          page_chunks = chunk_model.get_poject_chunks(project_id=project.id, page_no=page_no)
          if len(page_chunks):
               page_no +=1
          if not page_chunks or len(page_chunks) == 0:
               has_recorsd = False
               break

          is_inserted = nlp_controller.index_into_vector_db(project=project,
                                                  chunks=page_chunks,
                                                  do_reset=push_request.do_reset)
          if not is_inserted:
               return JSONResponse(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    contents ={ "signal" :ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value }
               )
          
          inseerted_item_count += len(page_chunks)

          return JSONResponse(
               contents ={ "signal" :ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
                          "inseerted_item_count" : inseerted_item_count }
          )