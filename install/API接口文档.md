# AI智能学习系统 - API接口文档

## 接口概述

本文档详细描述了AI智能学习系统的所有REST API接口，包括请求方法、参数、响应格式和示例代码。所有接口均采用JSON格式进行数据交换，并使用JWT令牌进行身份认证。

### 基础信息

- **Base URL**: `http://localhost:5001/api` (更新后的端口)
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`
- **字符编码**: UTF-8
- **版本**: v1.2.0
- **最后更新**: 2025-01-15

### 通用响应格式

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

## 1. 认证接口 (Authentication)

### 1.1 用户注册

**接口地址**: `POST /auth/register`

**请求参数**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "张三",
  "phone": "13800138000",
  "tenant_id": "tenant_001"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "user_id": "user_001",
    "email": "user@example.com",
    "username": "张三",
    "status": "pending_verification"
  }
}
```

### 1.2 用户登录

**接口地址**: `POST /auth/login`

**请求参数**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600,
    "user": {
      "id": "user_001",
      "email": "user@example.com",
      "username": "张三",
      "role": "student"
    }
  }
}
```

### 1.3 刷新令牌

**接口地址**: `POST /auth/refresh`

**请求头**:
```
Authorization: Bearer <refresh_token>
```

**响应示例**:
```json
{
  "success": true,
  "message": "令牌刷新成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600
  }
}
```

### 1.4 用户登出

**接口地址**: `POST /auth/logout`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "message": "登出成功"
}
```

## 2. 用户管理接口 (Users)

### 2.1 获取用户信息

**接口地址**: `GET /users/profile`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "user_001",
    "email": "user@example.com",
    "username": "张三",
    "phone": "13800138000",
    "avatar": "https://example.com/avatar.jpg",
    "role": "student",
    "tenant_id": "tenant_001",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-20T10:30:00Z"
  }
}
```

### 2.2 更新用户信息

**接口地址**: `PUT /users/profile`

**请求参数**:
```json
{
  "username": "李四",
  "phone": "13900139000",
  "avatar": "https://example.com/new_avatar.jpg"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "用户信息更新成功",
  "data": {
    "id": "user_001",
    "username": "李四",
    "phone": "13900139000",
    "avatar": "https://example.com/new_avatar.jpg"
  }
}
```

### 2.3 修改密码

**接口地址**: `PUT /users/password`

**请求参数**:
```json
{
  "old_password": "old_password123",
  "new_password": "new_password456"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

### 2.4 获取用户个人资料 🆕

**接口地址**: `GET /users/profile/details`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "user_001",
    "email": "user@example.com",
    "username": "张三",
    "nickname": "小明",
    "phone": "13800138000",
    "avatar": "https://example.com/avatar.jpg",
    "bio": "热爱学习的学生",
    "learning_preferences": {
      "preferred_subjects": ["数学", "物理"],
      "study_time": "evening",
      "difficulty_level": "intermediate"
    },
    "privacy_settings": {
      "show_email": false,
      "show_phone": false,
      "allow_ai_personalization": true
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-20T10:30:00Z"
  }
}
```

### 2.5 更新用户个人资料 🆕

**接口地址**: `PUT /users/profile/details`

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:
```json
{
  "username": "李四",
  "nickname": "小李",
  "phone": "13900139000",
  "bio": "积极向上的学习者",
  "learning_preferences": {
    "preferred_subjects": ["数学", "化学"],
    "study_time": "morning",
    "difficulty_level": "advanced"
  },
  "privacy_settings": {
    "show_email": true,
    "show_phone": false,
    "allow_ai_personalization": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "个人资料更新成功",
  "data": {
    "id": "user_001",
    "username": "李四",
    "nickname": "小李",
    "phone": "13900139000",
    "bio": "积极向上的学习者",
    "updated_at": "2024-01-20T11:00:00Z"
  }
}
```

### 2.6 上传用户头像 🆕

**接口地址**: `POST /users/profile/avatar`

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**请求参数**:
- `avatar`: 头像文件 (支持JPG、PNG格式，最大2MB)

**响应示例**:
```json
{
  "success": true,
  "message": "头像上传成功",
  "data": {
    "avatar_url": "https://example.com/avatars/user_001_1642680600.jpg",
    "updated_at": "2024-01-20T11:30:00Z"
  }
}
```

## 3. 学科管理接口 (Subjects)

### 3.1 获取学科列表

**接口地址**: `GET /subjects`

**查询参数**:
- `page`: 页码 (默认: 1)
- `per_page`: 每页数量 (默认: 20)
- `search`: 搜索关键词

**响应示例**:
```json
{
  "success": true,
  "data": {
    "subjects": [
      {
        "id": "subject_001",
        "name": "数学",
        "description": "初中数学课程",
        "grade_level": "初中",
        "chapters_count": 12,
        "knowledge_points_count": 156,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 50,
      "pages": 3
    }
  }
}
```

### 3.2 获取学科详情

**接口地址**: `GET /subjects/{subject_id}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "subject_001",
    "name": "数学",
    "description": "初中数学课程",
    "grade_level": "初中",
    "chapters": [
      {
        "id": "chapter_001",
        "name": "有理数",
        "order": 1,
        "knowledge_points_count": 15
      }
    ]
  }
}
```

### 3.3 创建学科

**接口地址**: `POST /subjects`

**请求参数**:
```json
{
  "name": "物理",
  "description": "初中物理课程",
  "grade_level": "初中"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "学科创建成功",
  "data": {
    "id": "subject_002",
    "name": "物理",
    "description": "初中物理课程",
    "grade_level": "初中"
  }
}
```

## 4. 知识点管理接口 (Knowledge Points)

### 4.1 获取知识点列表

**接口地址**: `GET /knowledge-points`

**查询参数**:
- `subject_id`: 学科ID
- `chapter_id`: 章节ID
- `difficulty`: 难度等级 (1-5)
- `page`: 页码
- `per_page`: 每页数量

**响应示例**:
```json
{
  "success": true,
  "data": {
    "knowledge_points": [
      {
        "id": "kp_001",
        "name": "有理数的概念",
        "description": "理解有理数的定义和分类",
        "difficulty": 2,
        "subject_id": "subject_001",
        "chapter_id": "chapter_001",
        "prerequisites": ["kp_000"],
        "learning_objectives": [
          "掌握有理数的定义",
          "能够分类有理数"
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 156,
      "pages": 8
    }
  }
}
```

### 4.2 获取知识点详情

**接口地址**: `GET /knowledge-points/{kp_id}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "kp_001",
    "name": "有理数的概念",
    "description": "理解有理数的定义和分类",
    "difficulty": 2,
    "content": "有理数是可以表示为两个整数之比的数...",
    "examples": [
      {
        "title": "例题1",
        "content": "判断下列数字是否为有理数...",
        "solution": "解题步骤..."
      }
    ],
    "related_points": ["kp_002", "kp_003"]
  }
}
```

## 5. 题目管理接口 (Questions)

### 5.1 获取题目列表

**接口地址**: `GET /questions`

**查询参数**:
- `subject_id`: 学科ID
- `knowledge_point_id`: 知识点ID
- `type`: 题目类型 (choice, fill, essay, judge)
- `difficulty`: 难度等级
- `page`: 页码
- `per_page`: 每页数量

**响应示例**:
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "id": "q_001",
        "type": "choice",
        "difficulty": 3,
        "content": "下列哪个数是有理数？",
        "options": [
          {"key": "A", "value": "π"},
          {"key": "B", "value": "√2"},
          {"key": "C", "value": "1/3"},
          {"key": "D", "value": "e"}
        ],
        "correct_answer": "C",
        "knowledge_points": ["kp_001"],
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 500,
      "pages": 25
    }
  }
}
```

### 5.2 获取题目详情

**接口地址**: `GET /questions/{question_id}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "q_001",
    "type": "choice",
    "difficulty": 3,
    "content": "下列哪个数是有理数？",
    "options": [
      {"key": "A", "value": "π"},
      {"key": "B", "value": "√2"},
      {"key": "C", "value": "1/3"},
      {"key": "D", "value": "e"}
    ],
    "correct_answer": "C",
    "explanation": "有理数是可以表示为分数形式的数，1/3是分数，因此是有理数。",
    "solution_steps": [
      "分析各选项的数学性质",
      "判断是否可以表示为分数形式",
      "得出正确答案"
    ],
    "knowledge_points": ["kp_001"],
    "tags": ["基础概念", "分类判断"]
  }
}
```

### 5.3 创建题目

**接口地址**: `POST /questions`

**请求参数**:
```json
{
  "type": "choice",
  "difficulty": 3,
  "content": "新题目内容",
  "options": [
    {"key": "A", "value": "选项A"},
    {"key": "B", "value": "选项B"},
    {"key": "C", "value": "选项C"},
    {"key": "D", "value": "选项D"}
  ],
  "correct_answer": "A",
  "explanation": "解题说明",
  "knowledge_points": ["kp_001"],
  "tags": ["标签1", "标签2"]
}
```

## 6. 诊断接口 (Diagnosis)

### 6.1 创建诊断测试

**接口地址**: `POST /diagnosis/create`

**请求参数**:
```json
{
  "subject_id": "subject_001",
  "test_type": "comprehensive",
  "knowledge_points": ["kp_001", "kp_002"],
  "difficulty_range": [1, 5],
  "question_count": 20
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "诊断测试创建成功",
  "data": {
    "diagnosis_id": "diag_001",
    "questions": [
      {
        "id": "q_001",
        "content": "题目内容",
        "type": "choice",
        "options": [...]
      }
    ],
    "time_limit": 1800,
    "created_at": "2024-01-20T10:30:00Z"
  }
}
```

### 6.2 提交诊断答案

**接口地址**: `POST /diagnosis/{diagnosis_id}/submit`

**请求参数**:
```json
{
  "answers": [
    {
      "question_id": "q_001",
      "answer": "C",
      "time_spent": 45
    },
    {
      "question_id": "q_002",
      "answer": "解答内容",
      "time_spent": 120
    }
  ],
  "total_time": 1650
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "诊断答案提交成功",
  "data": {
    "diagnosis_id": "diag_001",
    "score": 85,
    "correct_count": 17,
    "total_count": 20,
    "analysis_status": "processing"
  }
}
```

### 6.3 获取诊断报告

**接口地址**: `GET /diagnosis/{diagnosis_id}/report`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "diagnosis_id": "diag_001",
    "overall_score": 85,
    "ability_analysis": {
      "computation": 90,
      "reasoning": 80,
      "application": 85,
      "comprehension": 88
    },
    "knowledge_mastery": [
      {
        "knowledge_point_id": "kp_001",
        "name": "有理数概念",
        "mastery_level": 0.9,
        "status": "mastered"
      },
      {
        "knowledge_point_id": "kp_002",
        "name": "有理数运算",
        "mastery_level": 0.7,
        "status": "needs_practice"
      }
    ],
    "weak_areas": [
      {
        "area": "分数运算",
        "score": 65,
        "suggestions": ["加强分数基本运算练习", "理解分数运算规则"]
      }
    ],
    "recommendations": [
      "重点复习分数运算相关知识点",
      "增加应用题练习",
      "建议每日练习30分钟"
    ]
  }
}
```

## 7. 学习路径接口 (Learning Path)

### 7.1 生成学习路径

**接口地址**: `POST /learning-path/generate`

**请求参数**:
```json
{
  "subject_id": "subject_001",
  "target_knowledge_points": ["kp_005", "kp_006"],
  "current_level": "beginner",
  "time_budget": 30,
  "learning_style": "visual"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "学习路径生成成功",
  "data": {
    "path_id": "path_001",
    "estimated_duration": 25,
    "difficulty_progression": "gradual",
    "steps": [
      {
        "step": 1,
        "knowledge_point_id": "kp_001",
        "name": "有理数概念",
        "type": "learning",
        "estimated_time": 60,
        "resources": [
          {
            "type": "video",
            "title": "有理数基础概念",
            "url": "https://example.com/video1"
          },
          {
            "type": "exercise",
            "title": "基础练习题",
            "question_count": 10
          }
        ]
      }
    ]
  }
}
```

### 7.2 获取学习路径详情

**接口地址**: `GET /learning-path/{path_id}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "path_id": "path_001",
    "subject_id": "subject_001",
    "status": "in_progress",
    "progress": 0.4,
    "current_step": 3,
    "total_steps": 8,
    "estimated_completion": "2024-02-15T00:00:00Z",
    "steps": [...]
  }
}
```

### 7.3 更新学习进度

**接口地址**: `PUT /learning-path/{path_id}/progress`

**请求参数**:
```json
{
  "step": 3,
  "status": "completed",
  "time_spent": 45,
  "score": 88
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "学习进度更新成功",
  "data": {
    "path_id": "path_001",
    "current_step": 4,
    "progress": 0.5,
    "next_step": {
      "step": 4,
      "knowledge_point_id": "kp_004",
      "name": "有理数比较"
    }
  }
}
```

## 8. 内容生成接口 (Content Generation)

### 8.1 生成练习题

**接口地址**: `POST /content/generate-questions`

**请求参数**:
```json
{
  "knowledge_point_id": "kp_001",
  "question_type": "choice",
  "difficulty": 3,
  "count": 5,
  "style": "application"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "题目生成成功",
  "data": {
    "questions": [
      {
        "content": "生成的题目内容",
        "type": "choice",
        "options": [...],
        "correct_answer": "B",
        "explanation": "解题说明"
      }
    ]
  }
}
```

### 8.2 生成学习资料

**接口地址**: `POST /content/generate-material`

**请求参数**:
```json
{
  "knowledge_point_id": "kp_001",
  "material_type": "summary",
  "length": "medium",
  "style": "student_friendly"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "学习资料生成成功",
  "data": {
    "title": "有理数概念总结",
    "content": "生成的学习资料内容...",
    "key_points": [
      "有理数的定义",
      "有理数的分类",
      "有理数的性质"
    ],
    "examples": [...]
  }
}
```

### 8.3 生成解题步骤

**接口地址**: `POST /content/generate-solution`

**请求参数**:
```json
{
  "question_id": "q_001",
  "detail_level": "detailed",
  "include_alternatives": true
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "解题步骤生成成功",
  "data": {
    "question_id": "q_001",
    "main_solution": {
      "steps": [
        "分析题目条件",
        "确定解题思路",
        "逐步计算",
        "验证答案"
      ],
      "detailed_explanation": "详细解题过程..."
    },
    "alternative_solutions": [
      {
        "method": "方法二",
        "steps": [...],
        "explanation": "另一种解题思路..."
      }
    ]
  }
}
```

## 9. AI助手接口 (AI Assistant) 🆕

### 9.1 发送消息给AI助手

**接口地址**: `POST /ai-assistant/chat`

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:
```json
{
  "message": "请帮我解释一下有理数的概念",
  "context": {
    "subject_id": "subject_001",
    "knowledge_point_id": "kp_001",
    "conversation_id": "conv_001"
  },
  "options": {
    "use_nickname": true,
    "response_style": "friendly",
    "include_examples": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message_id": "msg_001",
    "response": "你好小明！有理数是可以表示为两个整数之比的数，包括正整数、负整数、零和分数。比如：1, -2, 0, 1/2, -3/4 都是有理数。",
    "conversation_id": "conv_001",
    "user_nickname": "小明",
    "timestamp": "2024-01-20T10:30:00Z",
    "related_resources": [
      {
        "type": "knowledge_point",
        "id": "kp_001",
        "title": "有理数概念"
      }
    ]
  }
}
```

### 9.2 获取对话历史

**接口地址**: `GET /ai-assistant/conversations/{conversation_id}`

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `per_page`: 每页消息数量 (默认: 20)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_001",
    "messages": [
      {
        "message_id": "msg_001",
        "role": "user",
        "content": "请帮我解释一下有理数的概念",
        "timestamp": "2024-01-20T10:30:00Z"
      },
      {
        "message_id": "msg_002",
        "role": "assistant",
        "content": "你好小明！有理数是可以表示为两个整数之比的数...",
        "timestamp": "2024-01-20T10:30:15Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 10,
      "pages": 1
    }
  }
}
```

### 9.3 创建新对话

**接口地址**: `POST /ai-assistant/conversations`

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:
```json
{
  "title": "数学学习讨论",
  "subject_id": "subject_001",
  "initial_message": "我想学习有理数相关的知识"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "对话创建成功",
  "data": {
    "conversation_id": "conv_002",
    "title": "数学学习讨论",
    "subject_id": "subject_001",
    "created_at": "2024-01-20T11:00:00Z",
    "first_response": "你好小明！我很高兴帮助你学习有理数相关的知识。有理数是数学中的基础概念..."
  }
}
```

### 9.4 获取用户对话列表

**接口地址**: `GET /ai-assistant/conversations`

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `per_page`: 每页数量 (默认: 10)
- `subject_id`: 学科筛选 (可选)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "conversation_id": "conv_001",
        "title": "有理数概念学习",
        "subject_name": "数学",
        "message_count": 10,
        "last_message_time": "2024-01-20T10:30:00Z",
        "created_at": "2024-01-20T09:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 5,
      "pages": 1
    }
  }
}
```

### 9.5 删除对话

**接口地址**: `DELETE /ai-assistant/conversations/{conversation_id}`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "message": "对话删除成功"
}
```

## 10. PPT模板管理接口 (PPT Templates) 🆕

### 10.1 获取模板列表

**接口地址**: `GET /api/ppt-templates/list`

**查询参数**:
- `category`: 模板分类 (可选)
- `tenant_id`: 租户ID (默认: default)
- `page`: 页码 (默认: 1)
- `per_page`: 每页数量 (默认: 20)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "template_001",
        "name": "商务演示模板",
        "description": "适用于商业演示和项目汇报",
        "category": "business",
        "preview_image_path": "/uploads/previews/template_001.jpg",
        "is_default": true,
        "usage_count": 156,
        "created_at": "2024-01-20T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 15,
      "pages": 1
    }
  }
}
```

### 10.2 上传PPT模板

**接口地址**: `POST /api/ppt-templates/upload`

**请求类型**: `multipart/form-data`

**请求参数**:
- `file`: PPT模板文件 (.pptx 或 .potx)
- `name`: 模板名称
- `description`: 模板描述 (可选)
- `category`: 模板分类 (默认: general)
- `user_id`: 用户ID
- `tenant_id`: 租户ID (默认: default)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "template": {
      "id": "template_002",
      "name": "教育课件模板",
      "description": "适用于教学课件制作",
      "category": "education",
      "template_file_path": "/uploads/ppt_templates/template_002.pptx",
      "file_size": 2048576,
      "created_at": "2024-01-20T11:00:00Z"
    },
    "message": "模板上传成功"
  }
}
```

### 10.3 生成PPT

**接口地址**: `POST /ai-assistant/generate-ppt`

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:
```json
{
  "content": "制作一个关于数学函数的教学PPT，包含：1. 函数的定义 2. 函数的性质 3. 常见函数类型 4. 实际应用例题",
  "template_id": "template_001",
  "user_id": "user_001",
  "tenant_id": "default"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "ppt_id": "ppt_001",
    "download_url": "/api/ppt/download/ppt_001",
    "preview_url": "/api/ppt/preview/ppt_001",
    "file_name": "数学函数教学PPT.pptx",
    "pages_count": 8,
    "generated_at": "2024-01-20T12:00:00Z",
    "message": "PPT生成成功"
  }
}
```

### 10.4 下载模板

**接口地址**: `GET /api/ppt-templates/{template_id}/download`

**响应**: 直接返回PPT文件流

### 10.5 删除模板

**接口地址**: `DELETE /api/ppt-templates/{template_id}`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "message": "模板删除成功"
}
```

### 10.6 获取模板分类

**接口地址**: `GET /api/ppt-templates/categories`

**查询参数**:
- `tenant_id`: 租户ID (默认: default)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "value": "business",
        "label": "商务"
      },
      {
        "value": "education",
        "label": "教育"
      },
      {
        "value": "academic",
        "label": "学术"
      }
    ]
  }
}
```

## 11. 记忆强化接口 (Memory Enhancement)

### 11.1 创建记忆卡片

**接口地址**: `POST /memory/cards`

**请求参数**:
```json
{
  "knowledge_point_id": "kp_001",
  "card_type": "concept",
  "front_content": "什么是有理数？",
  "back_content": "可以表示为两个整数之比的数",
  "difficulty": 2
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "记忆卡片创建成功",
  "data": {
    "card_id": "card_001",
    "next_review": "2024-01-21T10:30:00Z",
    "interval": 1,
    "ease_factor": 2.5
  }
}
```

### 11.2 获取待复习卡片

**接口地址**: `GET /memory/cards/due`

**查询参数**:
- `limit`: 返回数量限制 (默认: 20)
- `subject_id`: 学科筛选

**响应示例**:
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "card_id": "card_001",
        "front_content": "什么是有理数？",
        "back_content": "可以表示为两个整数之比的数",
        "knowledge_point": "有理数概念",
        "due_time": "2024-01-20T10:30:00Z",
        "review_count": 3
      }
    ],
    "total_due": 15
  }
}
```

### 11.3 提交复习结果

**接口地址**: `POST /memory/cards/{card_id}/review`

**请求参数**:
```json
{
  "quality": 4,
  "response_time": 8,
  "difficulty_rating": 3
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "复习结果提交成功",
  "data": {
    "card_id": "card_001",
    "next_review": "2024-01-23T10:30:00Z",
    "new_interval": 3,
    "ease_factor": 2.6
  }
}
```

## 12. 考试接口 (Exams)

### 12.1 创建考试

**接口地址**: `POST /exams`

**请求参数**:
```json
{
  "title": "数学期中考试",
  "subject_id": "subject_001",
  "duration": 120,
  "question_count": 30,
  "difficulty_distribution": {
    "easy": 0.3,
    "medium": 0.5,
    "hard": 0.2
  },
  "knowledge_points": ["kp_001", "kp_002", "kp_003"],
  "start_time": "2024-01-25T09:00:00Z",
  "end_time": "2024-01-25T11:00:00Z"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "考试创建成功",
  "data": {
    "exam_id": "exam_001",
    "title": "数学期中考试",
    "status": "scheduled",
    "question_count": 30,
    "duration": 120
  }
}
```

### 12.2 开始考试

**接口地址**: `POST /exams/{exam_id}/start`

**响应示例**:
```json
{
  "success": true,
  "message": "考试开始",
  "data": {
    "exam_session_id": "session_001",
    "questions": [
      {
        "id": "q_001",
        "content": "题目内容",
        "type": "choice",
        "options": [...]
      }
    ],
    "time_limit": 7200,
    "start_time": "2024-01-25T09:00:00Z"
  }
}
```

### 12.3 提交考试答案

**接口地址**: `POST /exams/{exam_id}/submit`

**请求参数**:
```json
{
  "session_id": "session_001",
  "answers": [
    {
      "question_id": "q_001",
      "answer": "C"
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "考试答案提交成功",
  "data": {
    "exam_id": "exam_001",
    "session_id": "session_001",
    "score": 92,
    "rank": 5,
    "total_participants": 150
  }
}
```

## 13. 统计分析接口 (Analytics)

### 13.1 获取学习统计

**接口地址**: `GET /analytics/learning-stats`

**查询参数**:
- `period`: 统计周期 (day, week, month, year)
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_study_time": 1800,
    "questions_answered": 245,
    "accuracy_rate": 0.87,
    "knowledge_points_mastered": 23,
    "daily_stats": [
      {
        "date": "2024-01-20",
        "study_time": 120,
        "questions_count": 15,
        "accuracy": 0.9
      }
    ],
    "subject_breakdown": [
      {
        "subject_id": "subject_001",
        "subject_name": "数学",
        "study_time": 900,
        "progress": 0.65
      }
    ]
  }
}
```

### 13.2 获取能力分析

**接口地址**: `GET /analytics/ability-analysis`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "overall_ability": 78,
    "ability_dimensions": {
      "computation": 85,
      "reasoning": 72,
      "application": 80,
      "comprehension": 75
    },
    "growth_trend": [
      {
        "date": "2024-01-01",
        "score": 65
      },
      {
        "date": "2024-01-20",
        "score": 78
      }
    ],
    "strengths": ["计算能力强", "基础概念掌握好"],
    "weaknesses": ["逻辑推理需加强", "应用题解题思路不够清晰"]
  }
}
```

## 14. 系统配置接口 (System)

### 14.1 获取系统配置

**接口地址**: `GET /system/config`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "features": {
      "ai_generation": true,
      "memory_enhancement": true,
      "adaptive_testing": true
    },
    "limits": {
      "max_questions_per_exam": 100,
      "max_study_time_per_day": 480,
      "max_file_upload_size": 10485760
    },
    "supported_languages": ["zh-CN", "en-US"]
  }
}
```

### 14.2 健康检查

**接口地址**: `GET /system/health`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-20T10:30:00Z",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "ai_service": "healthy"
    },
    "metrics": {
      "response_time": 45,
      "memory_usage": 0.65,
      "cpu_usage": 0.23
    }
  }
}
```

## 错误代码说明

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| AUTH_001 | 401 | 未授权访问 |
| AUTH_002 | 401 | 令牌已过期 |
| AUTH_003 | 401 | 令牌无效 |
| VALID_001 | 400 | 请求参数验证失败 |
| VALID_002 | 400 | 必填字段缺失 |
| VALID_003 | 400 | 字段格式错误 |
| RESOURCE_001 | 404 | 资源不存在 |
| RESOURCE_002 | 409 | 资源已存在 |
| PERMISSION_001 | 403 | 权限不足 |
| RATE_LIMIT_001 | 429 | 请求频率超限 |
| SERVER_001 | 500 | 服务器内部错误 |
| AI_001 | 503 | AI服务不可用 |
| AI_002 | 500 | AI生成失败 |

## 使用示例

### JavaScript/Node.js 示例

```javascript
// 用户登录
const login = async (email, password) => {
  const response = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  if (data.success) {
    localStorage.setItem('access_token', data.data.access_token);
    return data.data.user;
  }
  throw new Error(data.error.message);
};

// 获取用户信息
const getUserProfile = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:5000/api/users/profile', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  return data.success ? data.data : null;
};

// 创建诊断测试
const createDiagnosis = async (subjectId, questionCount) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:5000/api/diagnosis/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      subject_id: subjectId,
      test_type: 'comprehensive',
      question_count: questionCount
    })
  });
  
  const data = await response.json();
  return data.success ? data.data : null;
};
```

### Python 示例

```python
import requests
import json

class AILearningAPI:
    def __init__(self, base_url='http://localhost:5000/api'):
        self.base_url = base_url
        self.access_token = None
    
    def login(self, email, password):
        """用户登录"""
        url = f"{self.base_url}/auth/login"
        data = {'email': email, 'password': password}
        
        response = requests.post(url, json=data)
        result = response.json()
        
        if result['success']:
            self.access_token = result['data']['access_token']
            return result['data']['user']
        else:
            raise Exception(result['error']['message'])
    
    def get_headers(self):
        """获取请求头"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_subjects(self, page=1, per_page=20):
        """获取学科列表"""
        url = f"{self.base_url}/subjects"
        params = {'page': page, 'per_page': per_page}
        
        response = requests.get(url, params=params, headers=self.get_headers())
        result = response.json()
        
        return result['data'] if result['success'] else None
    
    def create_diagnosis(self, subject_id, question_count=20):
        """创建诊断测试"""
        url = f"{self.base_url}/diagnosis/create"
        data = {
            'subject_id': subject_id,
            'test_type': 'comprehensive',
            'question_count': question_count
        }
        
        response = requests.post(url, json=data, headers=self.get_headers())
        result = response.json()
        
        return result['data'] if result['success'] else None

# 使用示例
api = AILearningAPI()
user = api.login('user@example.com', 'password123')
subjects = api.get_subjects()
diagnosis = api.create_diagnosis('subject_001', 25)
```

## 总结

本API文档详细描述了AI智能学习系统的所有接口，包括认证、用户管理、学科管理、诊断测试、学习路径、内容生成等核心功能。所有接口都遵循RESTful设计原则，使用JSON格式进行数据交换，并提供了完整的错误处理机制。

开发者可以根据本文档快速集成系统功能，构建个性化的学习应用。如有疑问或需要技术支持，请联系开发团队。