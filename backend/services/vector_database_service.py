# -*- coding: utf-8 -*-
"""
向量数据库服务
实现文档向量化存储和语义检索功能
"""

import os
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sqlite3
import pickle
import hashlib
from functools import lru_cache
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import faiss
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None
    faiss = None
from utils.logger import get_logger

logger = get_logger(__name__)

class VectorDatabaseService:
    """
    向量数据库服务
    负责文档的向量化存储、检索和相似度计算
    """

    def __init__(self, db_path: str = "vector_database.db", model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化向量数据库服务

        Args:
            db_path: 向量数据库文件路径
            model_name: 文本嵌入模型名称
        """
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = None
        self.faiss_index = None
        self.vector_id_mapping = {}  # FAISS索引ID到文档信息的映射
        self.query_cache = {}  # 查询缓存
        self.cache_size = 100
        self._model_loaded = False  # 模型加载状态标记
        self._init_database()
        # 延迟加载嵌入模型（在第一次使用时加载）
        # self._load_embedding_model()  # 注释掉立即加载
        # 延迟构建FAISS索引（在第一次搜索时构建）
        self._faiss_index_built = False

    def _init_database(self):
        """
        初始化向量数据库表结构
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建文档向量表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_vectors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,  -- 'document', 'exam_paper'
                    chunk_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(document_id, chunk_id)
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_id
                ON document_vectors(document_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_type
                ON document_vectors(document_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON document_vectors(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_composite
                ON document_vectors(document_type, created_at)
            """)

            conn.commit()
            conn.close()

            logger.info("向量数据库初始化成功")

        except Exception as e:
            logger.error(f"向量数据库初始化失败: {str(e)}")
            raise

    def _load_embedding_model(self):
        """
        加载文本嵌入模型（懒加载）
        """
        if self._model_loaded:
            return
            
        if SentenceTransformer is None:
            logger.error("sentence-transformers未安装，无法使用向量化功能")
            self.embedding_model = None
            return

        try:
            logger.info(f"开始加载嵌入模型 {self.model_name}...")
            self.embedding_model = SentenceTransformer(self.model_name)
            self._model_loaded = True
            logger.info(f"嵌入模型 {self.model_name} 加载成功")
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {str(e)}")
            # 使用备用模型
            try:
                self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                logger.info("使用备用嵌入模型")
            except Exception as e2:
                logger.error(f"备用嵌入模型也加载失败: {str(e2)}")
                self.embedding_model = None

    def add_document_vectors(self, document_id: str, document_type: str,
                           content_chunks: List[str], metadata: Optional[Dict] = None) -> bool:
        """
        添加文档向量到数据库

        Args:
            document_id: 文档ID
            document_type: 文档类型 ('document' 或 'exam_paper')
            content_chunks: 文档内容分块列表
            metadata: 文档元数据

        Returns:
            是否添加成功
        """
        try:
            # 懒加载嵌入模型
            self._load_embedding_model()
            
            if self.embedding_model is None:
                logger.error("嵌入模型未加载，无法添加文档向量")
                return False

            # 生成文本嵌入向量
            embeddings = self.embedding_model.encode(content_chunks)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 删除已存在的文档向量
            cursor.execute("DELETE FROM document_vectors WHERE document_id = ?", (document_id,))

            # 插入新的向量数据
            for i, (chunk, embedding) in enumerate(zip(content_chunks, embeddings)):
                chunk_id = f"{document_id}_chunk_{i}"
                embedding_blob = pickle.dumps(embedding)
                metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

                cursor.execute("""
                    INSERT INTO document_vectors
                    (document_id, document_type, chunk_id, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (document_id, document_type, chunk_id, chunk, embedding_blob, metadata_json))

            conn.commit()
            conn.close()

            logger.info(f"文档 {document_id} 的 {len(content_chunks)} 个向量块添加成功")
            return True

        except Exception as e:
            logger.error(f"添加文档向量失败: {str(e)}")
            return False

    def search_similar_documents(self, query: str, document_type: Optional[str] = None,
                               top_k: int = 5, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        基于语义相似度搜索文档（优化版本）

        Args:
            query: 查询文本
            document_type: 文档类型过滤 ('document', 'exam_paper' 或 None)
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值

        Returns:
            相似文档列表
        """
        try:
            # 懒加载嵌入模型
            self._load_embedding_model()
            
            if self.embedding_model is None:
                logger.error("嵌入模型未加载，无法进行语义搜索")
                return []

            # 延迟构建FAISS索引
            if not self._faiss_index_built and faiss is not None:
                self._build_faiss_index()

            # 检查查询缓存
            cache_key = self._get_cache_key(query, document_type, top_k, similarity_threshold)
            if cache_key in self.query_cache:
                logger.info("使用缓存的搜索结果")
                return self.query_cache[cache_key]

            # 使用FAISS索引进行快速搜索
            if self.faiss_index is not None and faiss is not None and self._faiss_index_built:
                results = self._search_with_faiss(query, document_type, top_k, similarity_threshold)
            else:
                # 回退到原始方法
                results = self._search_with_cosine_similarity(query, document_type, top_k, similarity_threshold)

            # 应用高级相关性排序
            results = self._apply_advanced_ranking(results, query)

            # 缓存结果
            if len(self.query_cache) >= self.cache_size:
                # 清理最旧的缓存项
                oldest_key = next(iter(self.query_cache))
                del self.query_cache[oldest_key]

            self.query_cache[cache_key] = results

            logger.info(f"优化搜索找到 {len(results)} 个相关结果")
            return results

        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")
            return []

    def delete_document_vectors(self, document_id: str) -> bool:
        """
        删除文档的所有向量

        Args:
            document_id: 文档ID

        Returns:
            是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM document_vectors WHERE document_id = ?", (document_id,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(f"删除文档 {document_id} 的 {deleted_count} 个向量块")
            return True

        except Exception as e:
            logger.error(f"删除文档向量失败: {str(e)}")
            return False

    def get_document_statistics(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 总向量数量
            cursor.execute("SELECT COUNT(*) FROM document_vectors")
            total_vectors = cursor.fetchone()[0]

            # 按文档类型统计
            cursor.execute("""
                SELECT document_type, COUNT(*)
                FROM document_vectors
                GROUP BY document_type
            """)
            type_stats = dict(cursor.fetchall())

            # 文档数量
            cursor.execute("SELECT COUNT(DISTINCT document_id) FROM document_vectors")
            total_documents = cursor.fetchone()[0]

            conn.close()

            return {
                'total_vectors': total_vectors,
                'total_documents': total_documents,
                'type_statistics': type_stats,
                'model_name': self.model_name
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

    def _split_text_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        将长文本分割成块

        Args:
            text: 原始文本
            chunk_size: 块大小（字符数）
            overlap: 重叠字符数

        Returns:
            文本块列表
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # 尝试在句号、问号、感叹号处分割
            if end < len(text):
                for i in range(len(chunk) - 1, max(0, len(chunk) - 100), -1):
                    if chunk[i] in '。？！\n':
                        chunk = chunk[:i + 1]
                        end = start + i + 1
                        break

            chunks.append(chunk.strip())
            start = end - overlap

            if start >= len(text):
                break

        return [chunk for chunk in chunks if chunk.strip()]

    def _build_faiss_index(self):
        """
        构建FAISS向量索引以提升搜索性能
        """
        try:
            if faiss is None:
                logger.info("FAISS未安装，使用传统搜索方法")
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT document_id, document_type, chunk_id, content, embedding, metadata
                FROM document_vectors
            """)

            results = cursor.fetchall()
            conn.close()

            if not results:
                logger.info("没有向量数据，跳过FAISS索引构建")
                return

            # 提取所有嵌入向量
            embeddings = []
            self.vector_id_mapping = {}

            for i, row in enumerate(results):
                document_id, doc_type, chunk_id, content, embedding_blob, metadata_json = row
                embedding = pickle.loads(embedding_blob)
                embeddings.append(embedding)

                self.vector_id_mapping[i] = {
                    'document_id': document_id,
                    'document_type': doc_type,
                    'chunk_id': chunk_id,
                    'content': content,
                    'metadata': json.loads(metadata_json)
                }

            # 构建FAISS索引
            embeddings_array = np.array(embeddings).astype('float32')
            dimension = embeddings_array.shape[1]

            # 使用IndexFlatIP（内积）索引，适合余弦相似度
            self.faiss_index = faiss.IndexFlatIP(dimension)

            # 归一化向量以使用内积计算余弦相似度
            # 注意：faiss.normalize_L2会就地修改数组
            if faiss is not None and embeddings_array is not None:
                faiss.normalize_L2(x=embeddings_array)  # type: ignore
                if self.faiss_index is not None:
                    self.faiss_index.add(x=embeddings_array)  # type: ignore
            else:
                logger.error("embeddings_array 为空")

            self._faiss_index_built = True

            logger.info(f"FAISS索引构建成功，包含 {len(embeddings)} 个向量")

        except Exception as e:
            logger.error(f"构建FAISS索引失败: {str(e)}")
            self.faiss_index = None

    def _get_cache_key(self, query: str, document_type: Optional[str], top_k: int, similarity_threshold: float) -> str:
        """
        生成查询缓存键
        """
        key_data = f"{query}_{document_type}_{top_k}_{similarity_threshold}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _search_with_faiss(self, query: str, document_type: Optional[str],
                          top_k: int, similarity_threshold: float) -> List[Dict[str, Any]]:
        """
        使用FAISS索引进行快速搜索
        """
        try:
            # 懒加载嵌入模型
            self._load_embedding_model()
            
            if faiss is None or self.embedding_model is None or self.faiss_index is None:
                return []

            # 生成查询向量
            query_embedding = self.embedding_model.encode([query])[0]
            query_vec = np.array([query_embedding]).astype('float32').reshape(1, -1)
            # 确保查询向量也被归一化
            if faiss is not None:
                faiss.normalize_L2(query_vec)  # type: ignore

            # 搜索最相似的向量
            search_k = min(top_k * 3, len(self.vector_id_mapping))  # 搜索更多候选项
            if search_k > 0 and self.faiss_index is not None and query_vec is not None:
                similarities, indices = self.faiss_index.search(query_vec, search_k)  # type: ignore
            else:
                similarities, indices = np.array([[]]), np.array([[]])

            results = []
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx == -1:  # FAISS返回-1表示无效索引
                    continue

                if similarity < similarity_threshold:
                    continue

                doc_info = self.vector_id_mapping[idx]

                # 应用文档类型过滤
                if document_type and doc_info['document_type'] != document_type:
                    continue

                results.append({
                    'document_id': doc_info['document_id'],
                    'document_type': doc_info['document_type'],
                    'chunk_id': doc_info['chunk_id'],
                    'content': doc_info['content'],
                    'similarity': float(similarity),
                    'metadata': doc_info['metadata']
                })

            return results[:top_k]

        except Exception as e:
            logger.error(f"FAISS搜索失败: {str(e)}")
            return []

    def _search_with_cosine_similarity(self, query: str, document_type: Optional[str],
                                     top_k: int, similarity_threshold: float) -> List[Dict[str, Any]]:
        """
        使用传统余弦相似度搜索（回退方法）
        """
        try:
            # 懒加载嵌入模型
            self._load_embedding_model()
            
            if cosine_similarity is None or self.embedding_model is None:
                logger.error("相似度计算库或嵌入模型未加载，无法进行搜索")
                return []

            # 生成查询向量
            query_embedding = self.embedding_model.encode([query])[0]

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 构建查询SQL
            if document_type:
                cursor.execute("""
                    SELECT document_id, document_type, chunk_id, content, embedding, metadata
                    FROM document_vectors
                    WHERE document_type = ?
                    ORDER BY created_at DESC
                """, (document_type,))
            else:
                cursor.execute("""
                    SELECT document_id, document_type, chunk_id, content, embedding, metadata
                    FROM document_vectors
                    ORDER BY created_at DESC
                """)

            results = cursor.fetchall()
            conn.close()

            if not results:
                return []

            # 计算相似度
            similarities = []
            for row in results:
                document_id, doc_type, chunk_id, content, embedding_blob, metadata_json = row

                # 反序列化嵌入向量
                embedding = pickle.loads(embedding_blob)

                # 计算余弦相似度
                query_vec = np.array(query_embedding).reshape(1, -1)
                doc_vec = np.array(embedding).reshape(1, -1)
                similarity = cosine_similarity(query_vec, doc_vec)[0][0]

                if similarity >= similarity_threshold:
                    similarities.append({
                        'document_id': document_id,
                        'document_type': doc_type,
                        'chunk_id': chunk_id,
                        'content': content,
                        'similarity': float(similarity),
                        'metadata': json.loads(metadata_json)
                    })

            # 按相似度排序并返回top_k结果
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"传统搜索失败: {str(e)}")
            return []

    def _apply_advanced_ranking(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        应用高级相关性排序算法
        """
        try:
            if not results:
                return results

            # 计算查询词在内容中的匹配度
            query_words = set(query.lower().split())

            for result in results:
                content = result['content'].lower()
                content_words = set(content.split())

                # 计算词汇重叠度
                word_overlap = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0

                # 计算内容长度权重（适中长度的内容更相关）
                content_length = len(result['content'])
                length_weight = 1.0
                if content_length < 50:
                    length_weight = 0.8  # 内容太短
                elif content_length > 1000:
                    length_weight = 0.9  # 内容太长

                # 计算文档类型权重
                type_weight = 1.0
                if result['document_type'] == 'document':
                    type_weight = 1.1  # 文档类型稍微优先

                # 综合评分
                original_similarity = result['similarity']
                enhanced_score = (
                    original_similarity * 0.7 +  # 语义相似度权重70%
                    word_overlap * 0.2 +         # 词汇匹配权重20%
                    length_weight * 0.05 +       # 长度权重5%
                    type_weight * 0.05            # 类型权重5%
                )

                result['enhanced_score'] = enhanced_score
                result['word_overlap'] = word_overlap

            # 按增强评分重新排序
            results.sort(key=lambda x: x['enhanced_score'], reverse=True)

            # 移除临时字段
            for result in results:
                result.pop('enhanced_score', None)
                result.pop('word_overlap', None)

            return results

        except Exception as e:
            logger.error(f"高级排序失败: {str(e)}")
            return results

    def rebuild_index(self) -> bool:
        """
        重建FAISS索引
        """
        try:
            self._faiss_index_built = False
            self._build_faiss_index()
            return True
        except Exception as e:
            logger.error(f"重建索引失败: {str(e)}")
            return False

    def clear_cache(self):
        """
        清空查询缓存
        """
        self.query_cache.clear()
        logger.info("查询缓存已清空")

# 创建全局实例
vector_db_service = VectorDatabaseService()
