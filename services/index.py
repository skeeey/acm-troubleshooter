# coding: utf-8

import logging
import time
from llama_index.core import VectorStoreIndex
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import Document
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url
from pydantic import BaseModel
from tools.loaders.markdown import load_product_docs, load_runbooks

logger = logging.getLogger(__name__)

class RunbookInfo(BaseModel):
    id: str
    name: str
    hash: str

class RAGService:
    def __init__(self, db_url: str, embed_dim: int, db_table="acm_docs"):
        url = make_url(db_url)
        self.vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            table_name=db_table,
            embed_dim=embed_dim,
            # HNSW (Hierarchical Navigable Small World)
            #  - hnsw_m: This parameter refers to the maximum number of bidirectional links created for
            #       every new element during the construction of the graph.
            #  - hnsw_ef_construction: This parameter is used during the index building phase.
            #       Higher efConstruction values lead to a higher quality of the graph and, consequently,
            #       more accurate search results. However, it also means the index building process will
            #       take more time.
            #  - hnsw_ef_search: This parameter is used during the search phase. Like efConstruction, a
            #       larger efSearch value results in more accurate search results at the cost of increased
            #       search time. This value should be equal or larger than k (the number of nearest neighbors
            #       you want to return)
            hnsw_kwargs={
                "hnsw_m": 16, 
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 64,
                "hnsw_dist_method": "vector_cosine_ops",
            },
        )
        self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
    
    def index_docs(self, product_docs_dir: str, runbooks_dir: str):
        docs = []
        if product_docs_dir is not None:
            logger.info("loading product docs from %s", product_docs_dir)
            docs.extend(load_product_docs(product_docs_dir))
        
        if runbooks_dir is not None:
            logger.info("loading runbooks from %s", runbooks_dir)
            docs.extend(load_runbooks(runbooks_dir))

        if len(docs) == 0:
            raise ValueError("there is no product docs or runbooks")

        logger.info("index docs (total=%d) to database ...", len(docs))
        start_time = time.time()
        for doc in docs:
            self.index.insert(doc)
        logger.info("docs indexed, time used %.3fs", (time.time() - start_time))
    
    def refresh_runbooks(self, runbooks: list[Document], version="2.12"):
        runbook_infos = self.list_runbooks(version)
        for runbook in runbooks:
            existing, runbook_info = self.runbook_exists(runbook_infos, runbook.doc_id)
            if existing:
                if runbook.metadata["hash"] == runbook_info.hash:
                    logger.info("runbook '%s' not changed", runbook.metadata["name"])
                    continue
                
                logger.info("update runbook '%s'", runbook.metadata["name"])
                self.index.update_ref_doc(runbook)
                continue
            
            self.index.insert(runbook)
            logger.info("insert new runbook '%s'", runbook.metadata["name"])

    def delete_runbooks(self, doc_id: str):
        self.index.delete_ref_doc(doc_id, delete_from_docstore=True)

    def list_runbooks(self, version="2.12") -> list[RunbookInfo]:
        logger.info("list runbooks ...")
        start_time = time.time()
        nodes = self.vector_store.get_nodes(filters=MetadataFilters(
            filters=[
                MetadataFilter(key="version", value=version),
                MetadataFilter(key="kind", value="runbooks"),
            ],
            condition="and",
        ))
        logger.info("runbooks listed, time used %.3fs", (time.time() - start_time))

        runbooks = []
        for node in nodes:
            doc_id = node.extra_info["id"]
            existing, _ = self.runbook_exists(runbooks, doc_id)
            if existing:
                continue
            doc_name = node.extra_info["name"]
            doc_hash = node.extra_info["hash"]
            runbooks.append(RunbookInfo(id=doc_id, name=doc_name, hash=doc_hash))
        return runbooks

    def retrieve(self, query: str, version="2.12", similarity_cutoff=0.7, kinds=None):
        metadata_filters = MetadataFilters(
            filters=[
                MetadataFilter(key="version", value=version),
            ],
            condition="and",
        )

        if kinds is not None:
            metadata_filters.filters.append(
                MetadataFilter(key="kind", value=kinds, operator="in")
            )

        retriever = self.index.as_retriever(
            similarity_top_k=10,
            vector_store_kwargs={"hnsw_ef_search": 300},
            filters=metadata_filters,
        )
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)]
        )

        logger.info("retrieve docs for '%s' ...", query)
        start_time = time.time()
        response = query_engine.query(query)
        logger.info("docs retrieved, time used %.3fs", (time.time() - start_time))
        return response

    def runbook_exists(self, runbooks: list[RunbookInfo], doc_id: str):
        for runbook in runbooks:
            if runbook.id == doc_id:
                return True, runbook
        return False, None
