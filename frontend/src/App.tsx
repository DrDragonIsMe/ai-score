import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import React from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './App.css';

import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Diagnosis from './pages/Diagnosis';
import Exam from './pages/Exam';
import LearningPath from './pages/LearningPath';
import Login from './pages/Login';
import Memory from './pages/Memory';
import MistakeBook from './pages/MistakeBook';
import Register from './pages/Register';
import SubjectManagement from './pages/SubjectManagement';
import StatisticsAnalysis from './components/StatisticsAnalysis';
import { useAuthStore } from './stores/authStore';

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
    return (
        <ConfigProvider locale={zhCN}>
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
                                        <Route path="/learning-path" element={<LearningPath />} />
                                        <Route path="/memory-cards" element={<Memory />} />
                                        <Route path="/mistake-book" element={<MistakeBook />} />
                                        <Route path="/exam" element={<Exam />} />
                                        <Route path="/analytics" element={<StatisticsAnalysis />} />
                                        <Route path="/profile" element={<div>个人资料页面开发中...</div>} />
                                        <Route path="/settings" element={<div>设置页面开发中...</div>} />
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
