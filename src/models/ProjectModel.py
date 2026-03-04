from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):
    def __init__(self, db_client : object):
        super().__init__(db_client = db_client)
        self.collection= self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
            
    async def create_project(self, project : Project):
    # add collection to databasse (insert_one=> take dict)
    # await to wait to collect data 
        result = await self.collection.insert_one(project.dict())
        project._id = result.inserted_id

        return project


    async def get_project_or_create_one(self, project_id: str):

        record = await self.collection.find_one(  # "find_one" => return dict
            {
                "project_id" : project_id
            }
        )
        if record is None:
            project = Project(project_id = project_id) # define project
            project = await self.create_project(project = project) # create project

            return project

        return Project(**record)  # "record" is dict so we need to split each value at this dict to pass to "Project"


    async def get_all_projects(self, page: int=1, page_size: int=10):  #killer func

        # count total number of ducoments.
        total_ducoments= await self.collection.count_documents({})

        # calculate total numbeer of pages 
        total_pages = total_ducoments // page_size

        if total_ducoments % page_size> 0:
            total_page =+ 1

        cursor = self.collection.find().skip((page - 1 ) * page_size).limit(page_size)  #collect data 
        
        Projects = []
        async for document in cursor :
            Projects.append(
                 Project(**document)
            )

        return Projects, total_pages