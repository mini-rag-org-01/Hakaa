from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import PgVectorTableSChemeEnums,PgVectorDistanceMethodEnums,PgVectorIndexTypeEnums
import logging 
from typing import List 
from models.db_schemes import RetrievedDocument
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import text as sql_text
import json

class PGVectorDBProvider(VectorDBInterface):

    def __init__(self, db_client, default_vector_size: int=786, distance_method: str=None, index_threshold: int=100):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_method = distance_method
        self.pgvector_table_prefix = PgVectorTableSChemeEnums._PREFIX.value

        self.logger = logging.getLogger("uvicorn")
        self.default_index_name = lambda collection_name : f'{collection_name}_vector_idx'
        self.index_threshold = index_threshold


    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(
                    sql_text(f"CREATE EXTENSION IF NOT EXISTS vector;"))
            await session.commit()

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str)-> bool:
        record = None
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text("SELECT * FROM pg_tables WHERE tablename = :collection_name")
                result = await session.execute(list_tbl, {'collection_name' : collection_name})
                record = result.scalar_one_or_none()
        return record

    async def list_all_collections(self) -> List:
        record = None
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text("SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix")
                result = await session.execute(list_tbl, {'prefix' : self.pgvector_table_prefix})
                record = result.scalars().all()        
        return record

    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client() as session:
            async with session.begin():
                tbl_info_sql = sql_text(f'''
                SELECT  schemaname, tablename, tableowner, tablespace, hasindexes
                FROM pg_tables
                WHERE tablename = :collection_name
                ''')
                count_sql = sql_text(f'SELECT COUNT(*) FROM "{collection_name}"')

                tbl_info = await session.execute(tbl_info_sql,{'collection_name' : collection_name})
                tbl_data = tbl_info.fetchone()
                if not tbl_data:
                    return None

                record_count_result = await session.execute(count_sql)
                record_count = record_count_result.scalar_one()
                return {
                    "table_info" : dict(tbl_data),
                    "record_count" : record_count,
                }
                


    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting Collection: {collection_name}")
                del_sql = sql_text(f"DROP TABLE IF EXISTS {collection_name}")
                await session.execute(del_sql)
                await session.commit()
        return True

    async def create_collection(self, collection_name: str,
                                embedding_size: int,
                                do_reset: bool=False):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f"Creating Collection: '{collection_name}'")
            async with self.db_client() as session:
                async with session.begin():
                    create_sql = sql_text(
                        f'CREATE TABLE "{collection_name}" ('
                            f'{PgVectorTableSChemeEnums.ID.value} bigserial PRIMARY KEY,'
                            f'{PgVectorTableSChemeEnums.TEXT.value} text,'
                            f'{PgVectorTableSChemeEnums.VECTOR.value} vector({embedding_size}),'
                            f'{PgVectorTableSChemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\','
                            f'{PgVectorTableSChemeEnums.CHUNK_ID.value} integer, '
                            f'FOREIGN KEY ({PgVectorTableSChemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)'
                        ')')
                    await session.execute(create_sql)
                    await session.commit()
            return True

        return False

    async def is_index_existed(self,collection_name:str):
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                check_sql = sql_text(f'''
                    SELECT 1 
                    from pg_indexes 
                    WHERE tablename = :collection_name
                    AND indexname = :index_name
                ''')
                results = await session.execute(check_sql,{'collection_name':collection_name,'index_name':index_name})
                return bool(results.scalar_one_or_none())

    async def create_vector_index(self,collection_name: str,
                                    index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        is_index_existed = await self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            self.logger.info(f"Index already existed: {collection_name}")
            return False
        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(f'SELECT COUNT(*) FROM "{collection_name}"')
                result = await session.execute(count_sql)
                records_count = result.scalar_one()

                if records_count < self.index_threshold:
                    self.logger.info(f"records is less than threshold {self.index_threshold} "
                                    f"so can't create vector index for collection {collection_name}")
                    return False

                self.logger.info(f"Creating vector index for collection {collection_name}")

                index_name = self.default_index_name(collection_name)
                create_idx_sql = sql_text(
                    f'CREATE INDEX "{index_name}" ON "{collection_name}" '
                    f'USING {index_type} ({PgVectorTableSChemeEnums.VECTOR.value} {self.distance_method}) '
                )
                await session.execute(create_idx_sql)
                await session.commit()
                self.logger.info(f"END: created vector index for collection {collection_name}")


    async def reset_vector_index(self, collection_name:str, 
                                    index_type:str=PgVectorIndexTypeEnums.HNSW.value) -> bool:

        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                drop_sql = sql_text(F'DROP INDEX IF EXISTS {index_name}')
                await session.execute(drop_sql)
                await session.commit()
                return await self.create_vector_index(collection_name=collection_name,index_type=index_type)




    async def insert_one(self, collection_name: str, text:str, vector:str,
                            metadata: dict=None,recored_id: str=None):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        if not recored_id:
            self.logger.error(f"Can not insert new record without chunk id: {collection_name}")
            return False
        async with self.db_client() as session:
            async with session.begin():
                insert_sql= sql_text(
                    f'INSERT INTO "{collection_name}"'
                            '('
                            f'{PgVectorTableSChemeEnums.TEXT.value}, '
                            f'{PgVectorTableSChemeEnums.VECTOR.value}, '
                            f'{PgVectorTableSChemeEnums.METADATA.value}, '
                            f'{PgVectorTableSChemeEnums.CHUNK_ID.value}, '
                            ')'
                            f'VALUES (:text, :vector, :metadata, :chunk_id')
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata is not None else {}
                await session.execute(insert_sql,
                {'text': text, 
                'vector': '[' + ','.join(str(v) for v in vector) +']',
                'metadata':metadata_json,
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

        async with self.db_client() as session:
            async with session.begin():
                for i in range(0,len(texts), batch_size):
                    batch_texts = texts[i:i+batch_size]
                    batch_vectors = vectors[i:i+batch_size]
                    batch_metadata = metadata[i:i+batch_size]
                    batch_recored_ids = recored_ids[i:i+batch_size]
                    values = []
                    for txt,vec,meta,rec_id in zip(batch_texts,batch_vectors,batch_metadata,batch_recored_ids):
                        metadata_json = json.dumps(meta, ensure_ascii=False) if meta is not None else {}
                        values.append({
                            'text': txt, 
                            'vector': '[' + ','.join(str(v) for v in vec) +']',
                            'metadata':metadata_json,
                            'chunk_id': rec_id
                        })
                    batch_insert_sql = sql_text(
                        f'INSERT INTO "{collection_name}" ('
                                f'{PgVectorTableSChemeEnums.TEXT.value}, '
                                f'{PgVectorTableSChemeEnums.VECTOR.value}, '
                                f'{PgVectorTableSChemeEnums.METADATA.value}, '
                                f'{PgVectorTableSChemeEnums.CHUNK_ID.value} '
                                f') VALUES (:text, :vector, :metadata, :chunk_id)')
                    await session.execute(batch_insert_sql, values)
        return True

    
    async def search_by_vector(self, collection_name: str,vector: list, limit: int):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not search in non-existed collection: {collection_name}")
            return []
        vector = '[' + ','.join(str(v) for v in vector) +']',

        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(f'SELECT {PgVectorTableSChemeEnums.TEXT.value} AS text,'
                                        '1 - {PgVectorTableSChemeEnums.VECTOR.value} AS score,'
                                        'FROM {collection_name}'
                                        'ORDER BY sccore DESC'
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