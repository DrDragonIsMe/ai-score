import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import React from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './App.css';

import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Diagnosis from './pages/Diagnosis';
import Exam from './pages/Exam';
import ExamPaperManagement from './pages/ExamPaperManagement';
import LearningPath from './pages/LearningPath';
import Login from './pages/Login';
import Memory from './pages/Memory';
import MistakeBook from './pages/MistakeBook';
import Profile from './pages/Profile';
import Register from './pages/Register';
import Settings from './pages/Settings';
import SubjectManagement from './pages/SubjectManagement';
import LearningAnalytics from './pages/LearningAnalytics';
import DocumentManagement from './pages/DocumentManagement';
import { useAuthStore } from './stores/authStore';
import { useThemeStore, themeStyles } from './stores/themeStore';

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuthStore();
    return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// 公共路由组件（已登录用户重定向到仪表盘）
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuthStore();
    return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />;
};

const App: React.FC = () => {
    const { config, actualMode } = useThemeStore();
    const currentThemeStyle = themeStyles[config.style];
    const colors = config.customColors || currentThemeStyle.colors;

    // 构建Ant Design主题配置
    const antdTheme = {
        algorithm: actualMode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
            colorPrimary: colors.primary,
            colorInfo: colors.primary,
            colorSuccess: colors.secondary,
            colorWarning: '#faad14',
            colorError: '#ff4d4f',
            borderRadius: 8,
            wireframe: false,
        },
        components: {
            Layout: {
                bodyBg: actualMode === 'dark' ? '#141414' : '#f8f9fa',
                siderBg: actualMode === 'dark' ? '#1f1f1f' : 'linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%)',
                headerBg: actualMode === 'dark' ? '#1f1f1f' : '#ffffff',
            },
            Menu: {
                itemBg: 'transparent',
                itemSelectedBg: actualMode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(108, 123, 149, 0.12)',
                itemHoverBg: actualMode === 'dark' ? 'rgba(255, 255, 255, 0.06)' : 'rgba(108, 123, 149, 0.08)',
            },
            Card: {
                colorBgContainer: actualMode === 'dark' ? '#1f1f1f' : 'rgba(255, 255, 255, 0.9)',
            },
        },
    };

    return (
        <ConfigProvider locale={zhCN} theme={antdTheme}>
            <Router>
                <Routes>
                    {/* 公共路由 */}
                    <Route
                        path="/login"
                        element={
                            <PublicRoute>
                                <Login />
                            </PublicRoute>
                        }
                    />
                    <Route
                        path="/register"
                        element={
                            <PublicRoute>
                                <Register />
                            </PublicRoute>
                        }
                    />

                    {/* 受保护的路由 */}
                    <Route
                        path="/*"
                        element={
                            <ProtectedRoute>
                                <MainLayout>
                                    <Routes>
                                        <Route path="/dashboard" element={<Dashboard />} />
                                        <Route path="/diagnosis" element={<Diagnosis />} />
                                        <Route path="/subjects" element={<SubjectManagement />} />
                                        <Route path="/exam-papers" element={<ExamPaperManagement />} />
                                        <Route path="/documents" element={<DocumentManagement />} />
                                        <Route path="/learning-path" element={<LearningPath />} />
                                        <Route path="/memory-cards" element={<Memory />} />
                                        <Route path="/mistake-book" element={<MistakeBook />} />
                                        <Route path="/exam" element={<Exam />} />
                                        <Route path="/analytics" element={<LearningAnalytics />} />
                                        <Route path="/profile" element={<Profile />} />
                                        <Route path="/settings" element={<Settings />} />
                                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                                    </Routes>
                                </MainLayout>
                            </ProtectedRoute>
                        }
                    />
                </Routes>
            </Router>
        </ConfigProvider>
    );
};

export default App;
