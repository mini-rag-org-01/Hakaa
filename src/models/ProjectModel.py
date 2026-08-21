from .BaseDataModel import BaseDataModel
from .db_schemes.minirag.schemes import Project
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client) # class init
        return instance

    async def create_project(self, project: Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        return project

    async def get_project_or_create_one(self, project_id: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id==project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                if project == None:
                    # create project
                    project_rec = Project(
                        project_id = project_id
                    )
                    project = await self.create_project(project=project_rec)
                    return project
                else:
                    return project
    async def get_project_by_name(self, project_name: str):
        async with self.db_client() as session:
            query = (
                select(Project)
                .where(
                    func.lower(Project.project_name)
                    == project_name.strip().lower()
                )
                .limit(1)
            )

            result = await session.execute(query)
            return result.scalar_one_or_none()
    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        page = max(page, 1)
        page_size = max(page_size, 1)

        async with self.db_client() as session:
            count_result = await session.execute(
                select(func.count(Project.project_id))
            )
            total_projects = count_result.scalar_one()

            total_pages = (
                total_projects + page_size - 1
            ) // page_size

            query = (
                select(Project)
                .order_by(Project.project_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )

            result = await session.execute(query)
            projects = result.scalars().all()

            return projects, total_pages

    async def update_project(
        self,
        project_id: int,
        project_name=None,
        project_description=None,
        is_public=None,
        project_status=None,
        ):
        async with self.db_client() as session:
            query = select(Project).where(
                Project.project_id == project_id
            )

            result = await session.execute(query)
            project = result.scalar_one_or_none()

            if project is None:
                return None

            if project_name is not None:
                project.project_name = project_name

            if project_description is not None:
                project.project_description = project_description

            if is_public is not None:
                project.is_public = is_public

            if project_status is not None:
                project.project_status = project_status

            await session.commit()
            await session.refresh(project)

            return project

    async def get_public_projects(self):
        async with self.db_client() as session:
            query = (
                select(Project)
                .where(
                    Project.is_public.is_(True),
                    Project.project_status == "ready",
                    Project.project_name.is_not(None),
                )
                .order_by(Project.project_name)
            )

            result = await session.execute(query)
            return result.scalars().all()