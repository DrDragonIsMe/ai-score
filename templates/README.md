# 文件模板系统使用说明

## 概述

本系统提供了自动化的文件模板生成功能，可以从模板创建新文件并自动填入当天日期和其他动态信息。

## 文件结构

```
templates/
├── python_template.py          # Python文件模板
├── create_file_from_template.py # 模板生成器脚本
└── README.md                   # 使用说明（本文件）
```

## 使用方法

### 1. 使用脚本创建文件

```bash
# 基本语法
python templates/create_file_from_template.py <模板路径> <输出路径> <模块名称> <描述> [版本号]

# 示例：创建新的API文件（使用默认版本1.0.0）
python templates/create_file_from_template.py templates/python_template.py backend/api/new_feature.py "New Feature API" "处理新功能的API接口"

# 示例：创建新的服务文件（指定版本号）
python templates/create_file_from_template.py templates/python_template.py backend/services/new_service.py "New Service" "提供新功能的服务层实现" "2.1.0"

# 示例：创建带有特定版本的模块
python templates/create_file_from_template.py templates/python_template.py backend/utils/helper.py "Helper Utilities" "通用工具函数集合" "1.5.2"
```

### 2. 模板变量说明

模板文件中支持以下变量替换：

- `{MODULE_NAME}`: 模块名称
- `{DESCRIPTION}`: 模块描述
- `{DATE}`: 自动填入当天日期（格式：YYYY-MM-DD）
- `{VERSION}`: 版本号（可选参数，默认为1.0.0）

### 3. 生成的文件示例

使用模板生成的文件将包含以下格式的文件头：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能学习系统 - New Feature API

Description:
    处理新功能的API接口

Author: Chang Xinglong
Date: 2025-01-21  # 自动填入当天日期
Version: 2.1.0    # 根据参数动态填入版本号
License: Apache License 2.0
"""

# 在这里添加你的代码
```

## 特性

- ✅ **自动日期填充**: 每次创建文件时自动填入当天日期
- ✅ **模板变量替换**: 支持模块名称和描述的动态替换
- ✅ **目录自动创建**: 如果输出路径的目录不存在，会自动创建
- ✅ **错误处理**: 包含完善的错误处理和用户提示
- ✅ **编码支持**: 支持UTF-8编码，确保中文内容正确显示

## 扩展模板

如需添加新的模板类型，可以：

1. 在 `templates/` 目录下创建新的模板文件
2. 在模板中使用 `{变量名}` 格式定义需要替换的变量
3. 根据需要修改 `create_file_from_template.py` 脚本以支持新变量

## 注意事项

- 确保模板文件存在且可读
- 输出路径的父目录会自动创建
- 如果输出文件已存在，将被覆盖
- 所有文件都使用UTF-8编码