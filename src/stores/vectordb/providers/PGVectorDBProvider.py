from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import PgVectorTableSChemeEnums,PgVectorDistanceMethodEnums,PgVectorIndexTypeEnums
import logging 
from typing import List 
from models.db_schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json

class PgVectorDBProvider(VectorDBInterface):

    def __init__(self, db_client, default_vector_size: int=786, distance_method: str=None):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_method = distance_method
        self.pgvector_table_prefix = PgVectorTableSChemeEnums._PREFIX.value

        self.logger = logging.getLogger("uvicorn")

    async def connect(self):
        async with self.db_client as session:
            async with session.begin():
                await session.execute(
                    sql_text(f"CREATE EXTENSION IF NOT EXISTS vector;"))
            await session.commit()

    def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str)-> bool:
        record = None
        async with self.db_client as session:
            async with session.begin():
                list_tbl = sql_text("SELECT * FROM pg_tables WHERE tablename = :collection_name")
                result = await session.execute(list_tbl, {'collection_name' : collection_name})
                record = result.scalar_one_or_none()
        return record

    async def list_all_collections(self) -> List:
        record = None
        async with self.db_client as session:
            async with session.begin():
                list_tbl = sql_text("SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix")
                result = await session.execute(list_tbl, {'prefix' : self.pgvector_table_prefix})
                record = result.scalars().all()        
        return record

    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client as session:
            async with session.begin():
                tbl_info_sql = sql_text('''
                SELECT  chemaname, tablename, tableowner, tablespace, hasindexes
                FROM pg_tables
                WHERE tablename = :collection_name
                ''')
                count_sql = sql_text("SELECT COUNT(*) FROM :collection_name")

                tbl_info = await session.execute(tbl_info_sql, {'collection_name' : collection_name})
                record_count = await session.execute(count_sql, {'collection_name' : collection_name})
                tbl_data = tbl_info.fetchone()
                
                if not tbl_data:
                    return None

                return {
                    "table_info" : dict(tbl_data),
                    "record_count" : record_count,
                }
                


    async def delete_collection(self, collection_name: str):
        async with self.db_client as session:
            async with session.begin():
                self.logger.info(f"Deleting Collection: {collection_name}")
                del_sql = sql_text("DROP TABLE IF EXISTS:collection_name ")
                await session.execute(del_sql, {'collection_name': collection_name})
                await session.commit()
        return True

    async def create_collection(self, collection_name: str,
                                emdedding_size: int,
                                do_reset: bool=False):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f"Creating Collection: {collection_name}")
            async with self.db_client as session:
                async with session.begin():
                    create_sql = sql_text(
                        F'CREATE TABLE : {collection_name} ('
                            f'{PgVectorTableSChemeEnums.id.value} bigserial PRIMARY KEY,'
                            f'{PgVectorTableSChemeEnums.TEXT.value} text,'
                            f'{PgVectorTableSChemeEnums.VECTOR.value} vector({emdedding_size}),'
                            f'{PgVectorTableSChemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\','
                            f'{PgVectorTableSChemeEnums.CHUNK_ID.value} integer, '
                            f'FOREIGN KEY ({PgVectorTableSChemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)'
                        ')')
                    await session.execute(create_sql)
                    await session.commit()
            return True

        return False


    async def insert_one(self, collection_name: str, text:str, vector:str,
                            metadata: dict=None,recored_id: str=None):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        if not recored_id:
            self.logger.error(f"Can not insert new record without chunk id: {collection_name}")
            return False
        async with self.db_client as session:
            async with session.begin():
                insert_sql= sql_text(
                    f'INSERT INTO {collection_name}'
                            f'({PgVectorTableSChemeEnums.id.value},'
                            f'{PgVectorTableSChemeEnums.TEXT.value},'
                            f'{PgVectorTableSChemeEnums.VECTOR.value},'
                            f'{PgVectorTableSChemeEnums.METADATA.value},'
                            f'{PgVectorTableSChemeEnums.CHUNK_ID.value})'
                            f'VALUES (:text, :vector, :metadata, :chunk_id)')

                await session.execute(insert_sql,
                {'text': text, 
                'vector': '[' + ','.join(str(v) for v in vector) +']',
                'metadata':metadata,
                'chunk_id': recored_id})
                await session.commit()
        return True

    async def insert_many(self, collection_name: str,texts:list, vectors:list,
                            metadata: list=None,recored_ids: list=None,batch_size: int=50):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        if not len(vectors) == len(recored_ids):
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False

        if not metadata and len(metadata) == 0:
            metadata = [] * len(texts)
        async with self.db_client as session:
            async with session.begin():
                for i in range(0,len(texts), batch_size):
                    batch_texts = texts[i:i+batch_size]
                    batch_vectors = vectors[i:i+batch_size]
                    batch_metadata = metadata[i:i+batch_size]
                    batch_recored_ids = recored_ids[i:i+batch_size]
                    values = []
                    for txt,vec,meta,rec_id in zip(batch_texts,batch_vectors,batch_metadata,batch_recored_ids):
                        values.append({
                            'text': txt, 
                            'vector': '[' + ','.join(str(v) for v in vec) +']',
                            'metadata':meta,
                            'chunk_id': rec_id
                        })
                    batch_insert_sql = sql_text(
                        f'INSERT INTO {collection_name}'
                                f'{PgVectorTableSChemeEnums.id.value},'
                                f'{PgVectorTableSChemeEnums.TEXT.value},'
                                f'{PgVectorTableSChemeEnums.VECTOR.value},'
                                f'{PgVectorTableSChemeEnums.METADATA.value},'
                                f'{PgVectorTableSChemeEnums.CHUNK_ID.value}'
                                f'VALUES (:text, :vector, :metadata, :chunk_id)')
                    await session.execute(batch_insert_sql, values)
        return True

    
    async def search_by_vector(self, collection_name: str,vector: list, limit: int):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not search in non-existed collection: {collection_name}")
            return []
        vector = '[' + ','.join(str(v) for v in vector) +']',

        async with self.db_client as session:
            async with session.begin():
                search_sql = sql_text(f'SELECT from {PgVectorTableSChemeEnums.TEXT.value} as text,'
                                        '1 - {PgVectorTableSChemeEnums.VECTOR.value} as score,'
                                        'FROM {collection_name}'
                                        'ORDER BY sccore DEC'
                                        f'LIMIT {limit}') 
                result = await session.execute(search_sql, {'vector': vector})
                records = result.fitchall()

                return [
                    RetrievedDocument(
                        text=record.text,
                        score=record.score
                    )
                    for record in records
                ]