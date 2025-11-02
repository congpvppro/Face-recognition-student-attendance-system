import os
import faiss
import numpy as np
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Optional
from queue import Queue


class FaceDatabase:
    def __init__(self, embedding_size: int = 512, db_path: str = "./database/face_database", max_workers: int = 4) -> None:

        self.embedding_size = embedding_size
        self.db_path = db_path
        self.index_file = os.path.join(db_path, "faiss_index.bin")
        self.meta_file = os.path.join(db_path, "metadata.json")
        self.max_workers = max_workers
        self._shutdown = False

        os.makedirs(db_path, exist_ok=True)

        # Use inner product for cosine similarity search
        self.index = faiss.IndexFlatIP(embedding_size)

        # Thread-safe queue for batch processing
        self.search_queue = Queue()

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Use RLock instead of Lock to prevent potential deadlocks with nested locks
        self.lock = threading.RLock()

        # Stores associated names for each embedding
        self.metadata = []

    def add_face(self, embedding: np.ndarray, name: str) -> None:

        # normalized_embedding = embedding / np.linalg.norm(embedding)
        with self.lock:
            self.index.add(np.array([embedding], dtype=np.float32))
            self.metadata.append(name)

    def search(self, embedding: np.ndarray, threshold: float = 0.4) -> Tuple[str, float]:


        return self._search_internal(embedding, threshold)

    def _search_internal(self, embedding: np.ndarray, threshold: float = 0.4) -> Tuple[str, float]:

        if self.index.ntotal == 0:
            return "Unknown", 0.0

        normalized_embedding = embedding / np.linalg.norm(embedding)
        with self.lock:
            similarities, indices = self.index.search(np.array([normalized_embedding], dtype=np.float32), 1)

        similarity = float(similarities[0][0])
        idx = indices[0][0]

        if similarity > threshold and idx < len(self.metadata):
            return self.metadata[idx], similarity
        return "Unknown", similarity

    def batch_search(self, embeddings: List[np.ndarray], threshold: float = 0.4) -> List[Tuple[str, float]]:

        if not embeddings:
            return []

        if len(embeddings) < 10:
            with self.lock:
                results = []
                for embedding in embeddings:
                    result = self._search_internal(embedding, threshold)
                    results.append(result)
                return results
        else:
            return self.batch_search_parallel(embeddings, threshold)

    def batch_search_parallel(self, embeddings: List[np.ndarray], threshold: float = 0.4) -> List[Tuple[str, float]]:

        if self._shutdown:
            return self.batch_search(embeddings, threshold)

        futures = []
        for i, emb in enumerate(embeddings):
            future = self.executor.submit(self._search_internal, emb, threshold)
            futures.append((i, future))

        results = [None] * len(embeddings)
        for i, future in futures:
            try:
                results[i] = future.result()
            except Exception as e:
                logging.error(f"Error in batch search for embedding {i}: {e}")
                results[i] = ("Unknown", 0.0)

        return results

    def save(self) -> None:

        with self.lock:
            try:
                faiss.write_index(self.index, self.index_file)
                with open(self.meta_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2)
                logging.info(f"Face database saved with {self.index.ntotal} faces")
            except Exception as e:
                logging.error(f"Failed to save face database: {e}")
                raise

    def load(self) -> bool:
        if os.path.exists(self.index_file) and os.path.exists(self.meta_file):
            with self.lock:
                try:
                    self.index = faiss.read_index(self.index_file)
                    with open(self.meta_file, 'r', encoding='utf-8') as f:
                        self.metadata = json.load(f)
                    logging.info(f"Loaded face database with {self.index.ntotal} faces")
                    return True
                except Exception as e:
                    logging.error(f"Failed to load face database: {e}")
                    return False
        return False

    def _cleanup(self):
        if not self._shutdown:
            self._shutdown = True
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)

    def close(self):

        self._cleanup()

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self._cleanup()

    def __del__(self):

        try:
            self._cleanup()
        except:
            # Ignore errors during cleanup in destructor
            pass
