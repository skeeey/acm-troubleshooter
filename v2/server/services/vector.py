import logging
import time

from llama_index.core import VectorStoreIndex
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.schema import Document, NodeWithScore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self, db_url: str, embed_dim: int, db_table="vector_docs", hnsw_ef_search=300):
        url = make_url(db_url)
        self.vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            table_name=db_table,
            embed_dim=embed_dim,
            hnsw_kwargs={
                # max bidirectional links per node in the graph
                # higher = better recall + more memory; lower = faster indexing + less memory
                "hnsw_m": 16,
                # search width during index building, controls graph quality
                # higher = better graph quality + slower build; only paid once at index time
                "hnsw_ef_construction": 200,
                # search width at query time, must be >= top_k
                # higher = more accurate search + slower queries; overridden per query via retriever
                "hnsw_ef_search": 64,
                # distance metric; cosine similarity for normalized embeddings (BGE-M3)
                "hnsw_dist_method": "vector_cosine_ops",
            },
        )
        self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
        self.hnsw_ef_search = hnsw_ef_search
        # TODO: consider switching to bge-reranker-v2-m3 (lighter, multilingual, matches BGE-M3 embeddings)
        self.reranker = FlagEmbeddingReranker(model="BAAI/bge-reranker-large", top_n=3)

    def index_docs(self, docs: list[Document]):
        if len(docs) == 0:
            return

        start_time = time.time()
        for doc in docs:
            self.index.insert(doc)
        logger.info("docs indexed (total=%d), time=%.3fs", len(docs), time.time() - start_time)

    def delete_docs_by_source(self, source: str):
        nodes = self._get_nodes_by_source(source)
        ref_ids = {node.ref_doc_id for node in nodes}
        for ref_id in ref_ids:
            self.index.delete_ref_doc(ref_id, delete_from_docstore=True)

    def delete_docs_by_file(self, source: str, file_path: str):
        nodes = self._get_nodes_by_source(source)
        ref_ids = {node.ref_doc_id for node in nodes if node.extra_info.get("file_path") == file_path}
        for ref_id in ref_ids:
            self.index.delete_ref_doc(ref_id, delete_from_docstore=True)

    def list_file_hashes(self, source: str) -> dict[str, str]:
        nodes = self._get_nodes_by_source(source)
        file_hashes = {}
        for node in nodes:
            file_path = node.extra_info.get("file_path")
            content_hash = node.extra_info.get("content_hash")
            if file_path and content_hash and file_path not in file_hashes:
                file_hashes[file_path] = content_hash
        return file_hashes

    def retrieve(self, query: str, sources: list[str],
                 top_k=10, top_n=3, cutoff=0.3) -> list[NodeWithScore]:
        if not query or not query.strip():
            return []

        if not sources:
            raise ValueError("sources are required")

        metadata_filters = MetadataFilters(
            filters=[
                MetadataFilter(key="source", value=sources, operator="in"),
            ],
            condition="and",
        )

        retriever = self.index.as_retriever(
            similarity_top_k=top_k,
            vector_store_kwargs={"hnsw_ef_search": self.hnsw_ef_search},
            filters=metadata_filters,
        )

        start_time = time.time()
        nodes = retriever.retrieve(query)
        logger.info("retrieved (total=%d, top_k=%d), time=%.3fs",
                     len(nodes), top_k, time.time() - start_time)

        # low cutoff to let more candidates through to the reranker, which is more accurate
        processor = SimilarityPostprocessor(similarity_cutoff=cutoff)
        filtered_nodes = processor.postprocess_nodes(nodes)
        if len(filtered_nodes) == 0:
            return []

        self.reranker.top_n = top_n
        reranked_nodes = self.reranker.postprocess_nodes(filtered_nodes, query_str=query)

        # TODO: reconsider score > 0 filter; reranker scores differ from similarity scores
        return [node for node in reranked_nodes if node.score > 0]

    def _get_nodes_by_source(self, source: str):
        return self.vector_store.get_nodes(filters=MetadataFilters(
            filters=[MetadataFilter(key="source", value=source)],
            condition="and",
        ))
