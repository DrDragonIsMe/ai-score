import React, { useState, useEffect, useCallback } from 'react';
import {
  Upload,
  FileText,
  Download,
  Trash2,
  Eye,
  Search,
  Filter,
  Plus,
  FolderPlus,
  AlertCircle,
  CheckCircle,
  Clock,
  X
} from 'lucide-react';
import './DocumentManager.css';

// 辅助函数
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'processing':
      return <Clock className="w-4 h-4 text-yellow-500" />;
    case 'failed':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-500" />;
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed':
      return '解析完成';
    case 'processing':
      return '解析中';
    case 'failed':
      return '解析失败';
    default:
      return '等待解析';
  }
};

interface Document {
  id: string;
  filename: string;
  title: string;
  description?: string;
  file_size: number;
  file_type: string;
  parse_status: 'pending' | 'processing' | 'completed' | 'failed';
  parse_progress: number;
  created_at: string;
  updated_at: string;
  category?: {
    id: string;
    name: string;
  };
  tags: string[];
  page_count?: number;
  word_count?: number;
}

interface Category {
  id: string;
  name: string;
  description?: string;
  document_count?: number;
}

interface DocumentStats {
  total_documents: number;
  status_stats: {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  };
  type_stats: Record<string, number>;
}

const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);

  // 获取文档列表
  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: '20'
      });
      
      if (selectedCategory) {
        params.append('category_id', selectedCategory);
      }
      
      if (searchQuery) {
        params.append('search', searchQuery);
      }

      const response = await fetch(`/api/document/list?${params}`);
      const result = await response.json();
      
      if (result.success) {
        setDocuments(result.data.documents);
        setTotalPages(result.data.pages);
      } else {
        console.error('获取文档列表失败:', result.message);
      }
    } catch (error) {
      console.error('获取文档列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, selectedCategory, searchQuery]);

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/document/categories');
      const result = await response.json();
      
      if (result.success) {
        setCategories(result.data);
      }
    } catch (error) {
      console.error('获取分类列表失败:', error);
    }
  };

  // 获取统计信息
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/document/stats');
      const result = await response.json();
      
      if (result.success) {
        setStats(result.data);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 上传文档
  const handleUpload = async (file: File, title?: string, description?: string, categoryId?: string, tags?: string[]) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (title) formData.append('title', title);
      if (description) formData.append('description', description);
      if (categoryId) formData.append('category_id', categoryId);
      if (tags && tags.length > 0) formData.append('tags', tags.join(','));

      const response = await fetch('/api/document/upload', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        setShowUploadModal(false);
        fetchDocuments();
        fetchStats();
      } else {
        alert('上传失败: ' + result.message);
      }
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 删除文档
  const handleDelete = async (documentId: string) => {
    if (!confirm('确定要删除这个文档吗？')) return;
    
    try {
      const response = await fetch(`/api/document/${documentId}`, {
        method: 'DELETE'
      });
      
      const result = await response.json();
      
      if (result.success) {
        fetchDocuments();
        fetchStats();
      } else {
        alert('删除失败: ' + result.message);
      }
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败');
    }
  };

  // 下载文档
  const handleDownload = async (documentId: string, filename: string) => {
    try {
      const response = await fetch(`/api/document/${documentId}/download`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('下载失败');
      }
    } catch (error) {
      console.error('下载失败:', error);
      alert('下载失败');
    }
  };

  // 查看文档详情
  const handleViewDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/document/${documentId}`);
      const result = await response.json();
      
      if (result.success) {
        setSelectedDocument(result.data);
        setShowDocumentModal(true);
      } else {
        alert('获取文档详情失败: ' + result.message);
      }
    } catch (error) {
      console.error('获取文档详情失败:', error);
      alert('获取文档详情失败');
    }
  };

  // 创建分类
  const handleCreateCategory = async (name: string, description?: string) => {
    try {
      const response = await fetch('/api/document/categories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setShowCategoryModal(false);
        fetchCategories();
      } else {
        alert('创建分类失败: ' + result.message);
      }
    } catch (error) {
      console.error('创建分类失败:', error);
      alert('创建分类失败');
    }
  };



  useEffect(() => {
    fetchDocuments();
    fetchCategories();
    fetchStats();
  }, [fetchDocuments]);

  return (
    <div className="document-manager">
      {/* 页面头部 */}
      <div className="document-header">
        <div className="document-header-content">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="document-title">文档管理</h1>
              {stats && (
                <div className="document-stats">
                  <span>共 {stats.total_documents} 个文档</span>
                  <span className="separator">•</span>
                  <span>{stats.status_stats.completed} 已完成</span>
                  {stats.status_stats.processing > 0 && (
                    <>
                      <span className="separator">•</span>
                      <span className="processing">{stats.status_stats.processing} 处理中</span>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="document-actions">
              <button
                onClick={() => setShowCategoryModal(true)}
                className="btn-secondary"
              >
                <FolderPlus className="btn-icon" />
                分类
              </button>
              <button
                onClick={() => setShowUploadModal(true)}
                className="btn-primary"
              >
                <Upload className="btn-icon" />
                上传
              </button>
            </div>
          </div>
        </div>

        {/* 搜索和筛选 */}
        <div className="document-filters">
          <div className="filters-content">
            <div className="search-container">
              <div className="search-input-wrapper">
                <Search className="search-icon" />
                <input
                  type="text"
                  placeholder="搜索文档..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
              </div>
            </div>
            <div className="filter-controls">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="filter-select"
              >
                <option value="">所有分类</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* 文档列表 */}
        <div className="document-list">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p className="loading-text">加载中...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <FileText className="empty-icon" />
              <p className="empty-title">暂无文档</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="empty-action-btn"
              >
                上传第一个文档
              </button>
            </div>
          ) : (
            <div className="table-container">
              <table className="document-table">
                <thead className="table-header">
                  <tr>
                    <th className="table-th">
                      文档
                    </th>
                    <th className="table-th">
                      状态
                    </th>
                    <th className="table-th">
                      信息
                    </th>
                    <th className="table-th text-right">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="table-body">
                  {documents.map((document) => (
                    <tr key={document.id} className="table-row">
                      <td className="table-cell">
                        <div className="document-info">
                          <FileText className="document-icon" />
                          <div className="document-details">
                            <div className="document-list-title">
                              {document.title}
                            </div>
                            <div className="document-filename">
                              {document.filename}
                            </div>
                            {document.category && (
                              <span className="document-category">
                                {document.category.name}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="status-info">
                          {getStatusIcon(document.parse_status)}
                          <span className="status-text">
                            {getStatusText(document.parse_status)}
                          </span>
                        </div>
                        {document.parse_status === 'processing' && (
                          <div className="progress-container">
                            <div className="progress-bar">
                              <div
                                className="progress-fill"
                                style={{ width: `${document.parse_progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="table-cell">
                        <div className="file-size">
                          {formatFileSize(document.file_size)}
                        </div>
                        <div className="file-date">
                          {new Date(document.created_at).toLocaleDateString('zh-CN')}
                        </div>
                      </td>
                      <td className="table-cell text-right">
                        <div className="action-buttons">
                          <button
                            onClick={() => handleViewDocument(document.id)}
                            className="action-btn action-btn-view"
                            title="查看"
                          >
                            <Eye className="action-icon" />
                          </button>
                          <button
                            onClick={() => handleDownload(document.id, document.filename)}
                            className="action-btn action-btn-download"
                            title="下载"
                          >
                            <Download className="action-icon" />
                          </button>
                          <button
                            onClick={() => handleDelete(document.id)}
                            className="action-btn action-btn-delete"
                            title="删除"
                          >
                            <Trash2 className="action-icon" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="pagination-container">
              <div className="pagination-content">
                <div className="pagination-info">
                  第 {currentPage} 页，共 {totalPages} 页
                </div>
                <div className="pagination-buttons">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="pagination-btn"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="pagination-btn"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 上传文档模态框 */}
      {showUploadModal && (
        <UploadModal
          categories={categories}
          onUpload={handleUpload}
          onClose={() => setShowUploadModal(false)}
          uploading={uploading}
        />
      )}

      {/* 创建分类模态框 */}
      {showCategoryModal && (
        <CategoryModal
          onCreateCategory={handleCreateCategory}
          onClose={() => setShowCategoryModal(false)}
        />
      )}

      {/* 文档详情模态框 */}
      {showDocumentModal && selectedDocument && (
        <DocumentModal
          document={selectedDocument}
          onClose={() => {
            setShowDocumentModal(false);
            setSelectedDocument(null);
          }}
        />
      )}
    </div>
  );
};

// 上传文档模态框组件
interface UploadModalProps {
  categories: Category[];
  onUpload: (file: File, title?: string, description?: string, categoryId?: string, tags?: string[]) => void;
  onClose: () => void;
  uploading: boolean;
}

const UploadModal: React.FC<UploadModalProps> = ({ categories, onUpload, onClose, uploading }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [tags, setTags] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    if (!title) {
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      handleFileSelect(droppedFile);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    
    const tagList = tags.split(',').map(tag => tag.trim()).filter(tag => tag);
    onUpload(file, title, description, categoryId || undefined, tagList.length > 0 ? tagList : undefined);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container modal-container-lg">
        <div className="modal-header">
          <h2 className="modal-title">上传文档</h2>
          <button onClick={onClose} className="modal-close">
            <X className="close-icon" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-content">
          {/* 文件上传区域 */}
          <div
            className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
              dragOver ? 'border-blue-500 bg-blue-50' : file ? 'border-green-500 bg-green-50' : 'border-gray-300'
            }`}
            onDrop={handleDrop}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
          >
            {file ? (
              <div className="flex items-center justify-center">
                <FileText className="w-6 h-6 text-green-500 mr-2" />
                <div className="text-left">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
            ) : (
              <div>
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 mb-2">拖拽PDF文件到此处</p>
              </div>
            )}
            <label className="inline-block px-4 py-2 bg-blue-600 text-white text-sm rounded-md cursor-pointer hover:bg-blue-700 transition-colors">
              选择文件
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => {
                  const selectedFile = e.target.files?.[0];
                  if (selectedFile) handleFileSelect(selectedFile);
                }}
                className="hidden"
              />
            </label>
          </div>

          {/* 文档信息 - 紧凑布局 */}
          <div className="form-group">
            <div>
              <label className="form-label">
                标题 *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="form-input"
                placeholder="文档标题"
                required
              />
            </div>

            <div className="form-row">
              <div>
                <label className="form-label">
                  分类
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="form-select"
                >
                  <option value="">选择分类</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="form-label">
                  标签
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="form-input"
                  placeholder="用逗号分隔"
                />
              </div>
            </div>

            <div>
              <label className="form-label">
                描述
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="form-textarea"
                placeholder="文档描述（可选）"
              />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={uploading}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!file || uploading}
              className="btn-primary"
            >
              {uploading ? (
                <>
                  <div className="loading-spinner"></div>
                  上传中...
                </>
              ) : (
                '上传'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// 创建分类模态框组件
interface CategoryModalProps {
  onCreateCategory: (name: string, description?: string) => void;
  onClose: () => void;
}

const CategoryModal: React.FC<CategoryModalProps> = ({ onCreateCategory, onClose }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onCreateCategory(name.trim(), description.trim() || undefined);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container modal-container-sm">
        <div className="modal-header">
          <h3 className="modal-title">新建分类</h3>
          <button onClick={onClose} className="modal-close">
            <X className="close-icon" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-content">
          <div className="form-group">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="form-input"
              placeholder="分类名称"
              required
              autoFocus
            />
          </div>

          <div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="form-textarea"
              placeholder="描述（可选）"
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="btn-primary"
            >
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// 文档详情模态框组件
interface DocumentModalProps {
  document: Document & {
    pages?: Array<{
      id: string;
      page_number: number;
      page_content: string;
      content_type: string;
    }>;
    analyses?: Array<{
      id: string;
      analysis_type: string;
      result: any;
      confidence_score: number;
      status: string;
    }>;
  };
  onClose: () => void;
}

const DocumentModal: React.FC<DocumentModalProps> = ({ document, onClose }) => {
  const [activeTab, setActiveTab] = useState('info');

  return (
    <div className="modal-overlay">
      <div className="modal-container modal-container-xl">
        <div className="modal-header">
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-blue-500" />
            <div>
              <h3 className="modal-title truncate">{document.title}</h3>
              <p className="text-xs text-gray-500">{document.filename}</p>
            </div>
          </div>
          <button onClick={onClose} className="modal-close">
            <X className="close-icon" />
          </button>
        </div>

        {/* 标签页导航 */}
        <div className="modal-tabs">
          <nav className="tabs-nav">
            <button
              onClick={() => setActiveTab('info')}
              className={`tab-button ${
                activeTab === 'info' ? 'tab-button-active' : ''
              }`}
            >
              基本信息
            </button>
            {document.pages && document.pages.length > 0 && (
              <button
                onClick={() => setActiveTab('content')}
                className={`tab-button ${
                  activeTab === 'content' ? 'tab-button-active' : ''
                }`}
              >
                文档内容
              </button>
            )}
            {document.analyses && document.analyses.length > 0 && (
              <button
                onClick={() => setActiveTab('analysis')}
                className={`tab-button ${
                  activeTab === 'analysis' ? 'tab-button-active' : ''
                }`}
              >
                分析结果
              </button>
            )}
          </nav>
        </div>

        <div className="modal-content modal-content-scrollable">
          {activeTab === 'info' && (
            <div className="detail-content">
              <div className="detail-grid">
                <div className="detail-section">
                  <div className="detail-info-item">
                     <span className="detail-label">大小</span>
                     <span className="detail-value">{formatFileSize(document.file_size)}</span>
                   </div>
                  <div className="detail-info-item">
                    <span className="detail-label">页数</span>
                    <span className="detail-value">{document.page_count || 0}</span>
                  </div>
                  <div className="detail-info-item">
                    <span className="detail-label">字数</span>
                    <span className="detail-value">{document.word_count || 0}</span>
                  </div>
                </div>
                <div className="detail-section">
                  <div className="detail-info-item">
                    <span className="detail-label">上传</span>
                    <span className="detail-value">{new Date(document.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="detail-info-item">
                    <span className="detail-label">更新</span>
                    <span className="detail-value">{new Date(document.updated_at).toLocaleDateString()}</span>
                  </div>
                  <div className="detail-info-item">
                    <span className="detail-label">状态</span>
                    <div className="detail-status">
                      {getStatusIcon(document.parse_status)}
                      <span className="status-text">
                        {getStatusText(document.parse_status)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {document.description && (
                <div className="detail-description">
                  <h4 className="detail-section-title">描述</h4>
                  <p className="detail-description-text">{document.description}</p>
                </div>
              )}

              {document.tags.length > 0 && (
                <div className="detail-tags">
                  <h4 className="detail-section-title">标签</h4>
                  <div className="detail-tags-list">
                    {document.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="detail-tag"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'content' && document.pages && (
            <div className="content-tab">
              <div className="content-header">
                <h4 className="content-title">文档内容</h4>
                <span className="content-count">{document.pages.length} 页</span>
              </div>
              <div className="content-pages">
                {document.pages.map((page) => (
                  <div key={page.id} className="content-page">
                    <div className="page-header">
                      <span className="page-number">第 {page.page_number} 页</span>
                      <span className="page-chars">{(page.page_content || '').length} 字符</span>
                    </div>
                    <div className="page-content">
                      {page.page_content || '无内容'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'analysis' && document.analyses && (
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-gray-200">
                <h4 className="text-sm font-medium text-gray-900">分析结果</h4>
                <span className="text-xs text-gray-500">{document.analyses.length} 项</span>
              </div>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {document.analyses.map((analysis) => (
                  <div key={analysis.id} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">
                        {analysis.analysis_type === 'classification' ? '文档分类分析' : analysis.analysis_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        置信度: {(analysis.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 bg-white rounded border p-2 max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap font-mono leading-relaxed">
                        {JSON.stringify(analysis.result, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentManager;