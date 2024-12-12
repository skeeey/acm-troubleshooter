# coding: utf-8

import logging
import time
from llama_index.core import VectorStoreIndex
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import Document, NodeWithScore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.vector_stores.postgres import PGVectorStore
from pydantic import BaseModel
from sqlalchemy import make_url

logger = logging.getLogger(__name__)

class DocInfo(BaseModel):
    id: str
    name: str
    hash: str

class RAGService:
    def __init__(self, db_url: str, embed_dim: int, db_table="vector_docs",
                 similarity_cutoff=0.5, similarity_top_k=3, hnsw_ef_search=300):
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
        self.similarity_cutoff = similarity_cutoff
        self.similarity_top_k = similarity_top_k
        self.hnsw_ef_search = hnsw_ef_search
    
    def index_docs(self, docs: list[Document]):
        if len(docs) == 0:
            raise ValueError("there is no product docs or runbooks")

        start_time = time.time()
        for doc in docs:
            self.index.insert(doc)
        logger.debug("docs (total=%d) are indexed, time used %.3fs", len(docs), (time.time() - start_time))

    def delete_docs(self, source: str):
        doc_infos = self.list_docs(source)
        for doc_info in doc_infos:
            start_time = time.time()
            self.index.delete_ref_doc(doc_info.id, delete_from_docstore=True)
            logger.info("doc (%s) was deleted, time used %.3fs", doc_info.name, (time.time() - start_time))

    def list_docs(self, source: str) -> list[DocInfo]:
        start_time = time.time()
        nodes = self.vector_store.get_nodes(filters=MetadataFilters(
            filters=[
                MetadataFilter(key="source", value=source),
            ],
            condition="and",
        ))
        logger.info("docs (source=%s, total=%d) listed, time used %.3fs", source, len(nodes), (time.time() - start_time))

        docs = []
        for node in nodes:
            doc_id = node.ref_doc_id
            existing, _ = self.doc_exists(docs, doc_id)
            if existing:
                continue
            doc_name = node.extra_info["filename"]
            doc_hash = node.extra_info["hash"]
            docs.append(DocInfo(id=doc_id, name=doc_name, hash=doc_hash))
        return docs

    def retrieve(self, query: str, sources: list[str]=None) -> list[NodeWithScore]:
        if sources is None:
            raise ValueError("sources are required")
        
        metadata_filters = MetadataFilters(
            filters=[
                MetadataFilter(key="source", value=sources, operator="in"),
            ],
            condition="and",
        )

        retriever = self.index.as_retriever(
            similarity_top_k=self.similarity_top_k,
            vector_store_kwargs={"hnsw_ef_search": self.hnsw_ef_search},
            filters=metadata_filters,
        )
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=self.similarity_cutoff)]
        )

        start_time = time.time()
        response = query_engine.query(query)
        logger.debug("docs retrieved (total=%d, query=%s, sources=%s), time used %.3fs",
                    len(response.source_nodes), query, sources, (time.time() - start_time))
        nodes = []
        for node in response.source_nodes:
            logger.debug("-- doc: [%.3f] %s" % (node.score, node.metadata["filename"]))
            nodes.append(node)
        return nodes

    def doc_exists(self, docs: list[DocInfo], doc_id: str):
        for doc in docs:
            if doc.id == doc_id:
                return True, doc
        return False, None
