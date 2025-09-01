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
    <div className="p-6 max-w-7xl mx-auto">
      {/* 简化的页面头部 */}
      <div className="bg-white rounded-lg shadow-sm mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-900">文档管理</h1>
              {stats && (
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>共 {stats.total_documents} 个文档</span>
                  <span>•</span>
                  <span>{stats.status_stats.completed} 已完成</span>
                  {stats.status_stats.processing > 0 && (
                    <>
                      <span>•</span>
                      <span className="text-yellow-600">{stats.status_stats.processing} 处理中</span>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowCategoryModal(true)}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                <FolderPlus className="w-4 h-4 mr-1" />
                分类
              </button>
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
              >
                <Upload className="w-4 h-4 mr-1" />
                上传
              </button>
            </div>
          </div>
        </div>

        {/* 搜索和筛选 */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="flex-1 max-w-sm">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="搜索文档..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white"
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

        {/* 文档列表 */}
        <div className="">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-500">加载中...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 mb-3">暂无文档</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                上传第一个文档
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      文档
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      信息
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documents.map((document) => (
                    <tr key={document.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <FileText className="w-6 h-6 text-blue-500 mr-3 flex-shrink-0" />
                          <div className="min-w-0 flex-1">
                            <div className="text-sm font-medium text-gray-900 truncate">
                              {document.title}
                            </div>
                            <div className="text-xs text-gray-500 truncate">
                              {document.filename}
                            </div>
                            {document.category && (
                              <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                {document.category.name}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(document.parse_status)}
                          <span className="ml-2 text-sm text-gray-700">
                            {getStatusText(document.parse_status)}
                          </span>
                        </div>
                        {document.parse_status === 'processing' && (
                          <div className="mt-1 w-16">
                            <div className="w-full bg-gray-200 rounded-full h-1">
                              <div
                                className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                                style={{ width: `${document.parse_progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatFileSize(document.file_size)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(document.created_at).toLocaleDateString('zh-CN')}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end space-x-1">
                          <button
                            onClick={() => handleViewDocument(document.id)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 rounded transition-colors"
                            title="查看"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDownload(document.id, document.filename)}
                            className="p-1.5 text-gray-400 hover:text-green-600 rounded transition-colors"
                            title="下载"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(document.id)}
                            className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors"
                            title="删除"
                          >
                            <Trash2 className="w-4 h-4" />
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
            <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-500">
                  第 {currentPage} 页，共 {totalPages} 页
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-xs border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white transition-colors"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-xs border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white transition-colors"
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">上传文档</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
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
          <div className="grid grid-cols-1 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                标题 *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="文档标题"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  分类
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white"
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  标签
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="用逗号分隔"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="文档描述（可选）"
              />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              disabled={uploading}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!file || uploading}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-sm mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">新建分类</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          <div>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
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
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              placeholder="描述（可选）"
            />
          </div>

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-3xl mx-4 max-h-[85vh] overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 truncate">{document.title}</h3>
              <p className="text-xs text-gray-500">{document.filename}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 简化的标签页 */}
        <div className="border-b border-gray-200">
          <nav className="flex px-4">
            <button
              onClick={() => setActiveTab('info')}
              className={`py-2 px-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'info'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              信息
            </button>
            {document.pages && document.pages.length > 0 && (
              <button
                onClick={() => setActiveTab('content')}
                className={`py-2 px-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'content'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                内容
              </button>
            )}
            {document.analyses && document.analyses.length > 0 && (
              <button
                onClick={() => setActiveTab('analysis')}
                className={`py-2 px-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'analysis'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                分析
              </button>
            )}
          </nav>
        </div>

        <div className="p-4 overflow-y-auto max-h-[calc(85vh-140px)]">
          {activeTab === 'info' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                     <span className="text-sm text-gray-600">大小</span>
                     <span className="text-sm font-medium">{formatFileSize(document.file_size)}</span>
                   </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">页数</span>
                    <span className="text-sm font-medium">{document.page_count || 0}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">字数</span>
                    <span className="text-sm font-medium">{document.word_count || 0}</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">上传</span>
                    <span className="text-sm font-medium">{new Date(document.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">更新</span>
                    <span className="text-sm font-medium">{new Date(document.updated_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-600">状态</span>
                    <div className="flex items-center">
                      {getStatusIcon(document.parse_status)}
                      <span className="ml-2 text-sm font-medium">
                        {getStatusText(document.parse_status)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {document.description && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">描述</h4>
                  <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md leading-relaxed">{document.description}</p>
                </div>
              )}

              {document.tags.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">标签</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {document.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md border border-blue-200"
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
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-gray-200">
                <h4 className="text-sm font-medium text-gray-900">文档内容</h4>
                <span className="text-xs text-gray-500">{document.pages.length} 页</span>
              </div>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {document.pages.map((page) => (
                  <div key={page.id} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">第 {page.page_number} 页</span>
                      <span className="text-xs text-gray-500">{(page.page_content || '').length} 字符</span>
                    </div>
                    <div className="text-xs text-gray-600 whitespace-pre-wrap max-h-24 overflow-y-auto leading-relaxed">
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