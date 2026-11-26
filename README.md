# 📊 AI-Data-Analyst

一个基于 Python、Pandas 和 Streamlit 开发的智能数据分析助手，支持 CSV 数据导入、数据质量检测、数据清洗、统计分析和可视化展示。

## 一、项目简介

AI-Data-Analyst 是一个面向通用表格数据的分析工具，旨在帮助用户更方便地完成数据预览、质量检查、数据清洗和基础统计分析。

项目采用模块化设计，将页面交互、数据分析、数据质量检测、数据清洗和图表生成等功能拆分为独立模块。

## 二、当前已实现功能

### 1. 数据导入与预览

- 支持 CSV 文件上传。
- 展示数据内容。
- 统计数据行数和列数。
- 展示基础描述性统计信息。

### 2. 数据质量检测

- 缺失值数量及比例检测。
- 重复行检测。
- 基于 IQR 方法的异常值检测。
- 数据类型检查。

### 3. 数据清洗

- 删除包含缺失值的行。
- 使用均值填充缺失值。
- 使用中位数填充缺失值。
- 删除重复数据。
- 标记异常值。
- 异常值截断、删除及均值/中位数替换。
- 数据类型转换。

### 4. 数据对比与导出

- 对比清洗前后的数据行数和列数。
- 对比缺失值和重复行数量。
- 对比数据类型变化。
- 对比内存占用。
- 恢复原始数据。
- 下载原始数据和清洗后的 CSV 文件。

### 5. 数据分析与可视化

- 平均值、最大值、最小值等统计指标。
- 按专业进行分组统计。
- 按课程进行成绩分析。
- 专业平均成绩对比图。
- 课程平均成绩对比图。

### 6. AI 智能分析

- 接入 DeepSeek 大语言模型，支持用自然语言提问分析当前数据。
- 提问时自动附带数据统计摘要和数据质量提示（缺失值、重复记录、成绩异常等），不发送完整原始数据。
- API Key 通过本地 `.env` 文件中的 `DEEPSEEK_API_KEY` 配置，不写进代码。

### 7. MySQL 数据库连接与 SQL 查询

- 数据来源新增 MySQL：填写主机、端口、用户名、密码和数据库名即可连接（密码只用于本次连接，不保存）。
- 支持测试连接并列出当前数据库的全部表，可按表名加载整张表。
- 支持手写 SQL 查询：只允许 SELECT / WITH 开头的单条只读查询，增删改等语句会被拦截，结果最多返回 1000 行。
- 从 MySQL 加载的数据与 CSV 一样，可继续使用数据清洗、质量检测、统计分析和 AI 智能分析。

### 8. FastAPI 后端接口

新增 `api.py`，把 core 里的已有能力包装成 HTTP 接口（与 Streamlit 页面相互独立，只返回 JSON）：

- `GET /health`：健康检查；`GET /docs`：自动生成的交互式接口文档，可在线测试。
- `POST /data/upload`：上传 CSV，返回行列数和数据预览。
- `POST /data/quality`：上传 CSV，返回缺失值、重复行、IQR 异常值和数据类型报告。
- `POST /data/clean`：上传 CSV 并按指定操作清洗（去重、删缺失、均值/中位数填充、异常值标记/截断）。
- `POST /data/analyze-by-major`：按专业统计成绩。
- `POST /ai/ask`：上传 CSV 并用自然语言向 DeepSeek 提问（需配置 API Key）。
- `POST /database/query`：连接 MySQL 执行只读 SQL 查询（复用 database 模块的校验）。

启动方式：

```bash
uvicorn api:app --reload
```

启动后打开 `http://127.0.0.1:8000/docs` 即可查看和测试全部接口。

### 9. Pytest 自动化测试

- 测试套件位于 `tests/` 目录，共 51 个用例，覆盖数据清洗、数据质量检测、按专业统计、数据库只读查询校验和 FastAPI 全部接口。
- 测试使用 SQLite 内存库代替 MySQL、monkeypatch 代替 DeepSeek 调用，不需要真实服务器和 API Key，可离线重复运行。
- 在项目根目录运行：`python -m pytest`，全部通过时会显示 `51 passed`。

## 三、技术栈

| 技术         | 用途        |
| ---------- | --------- |
| Python     | 项目主要开发语言  |
| Pandas     | 数据处理与统计分析 |
| Streamlit  | Web 交互界面  |
| Matplotlib | 数据可视化     |
| SQLAlchemy | 数据库连接与查询 |
| FastAPI    | 后端 API 接口 |
| PyMySQL    | MySQL 驱动    |
| Pytest     | 自动化测试    |
| Git        | 版本管理      |
| GitHub     | 项目托管      |

## 四、项目结构

```text
AI-Data-Analyst/
├── app.py
├── api.py
├── requirements.txt
├── .gitignore
├── core/
│   ├── ai_analyzer.py
│   ├── data_analyzer.py
│   ├── chart_generator.py
│   ├── data_quality.py
│   ├── data_cleaner.py
│   └── database.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_data_cleaner.py
│   ├── test_data_quality.py
│   └── test_database.py
├── pytest.ini
└── data/
    ├── sample.csv
    └── test_quality.csv
```

## 五、本地运行

### 1. 克隆项目

```bash
git clone https://github.com/Elaina-liang/AI-Data-Analyst.git
```

### 2. 进入项目目录

```bash
cd AI-Data-Analyst
```

### 3. 创建虚拟环境

```bash
python -m venv venv
```

### 4. 激活虚拟环境

Windows PowerShell：

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 6. 启动项目

```bash
python -m streamlit run app.py
```

启动后，根据终端提示在浏览器中打开 Streamlit 页面。

### 7. 运行自动化测试（可选）

```bash
python -m pytest
```

## 六、后续开发计划

以下功能尚未完成，属于项目后续规划：

- [ ] 支持 Excel 文件导入。
- [ ] 增加更多通用数据分析方法。
- [ ] 增加更多数据可视化图表。
- [x] 接入大语言模型，实现自然语言数据分析。（已完成：接入 DeepSeek）
- [x] 增加 MySQL 数据库连接与 SQL 查询。（已完成）
- [x] 使用 FastAPI 构建后端接口。（已完成）
- [x] 增加 Pytest 自动化测试。（已完成：tests/ 目录 51 个用例，运行 `python -m pytest`）
- [ ] 完善项目部署和文档。

## 七、项目地址

GitHub：

[https://github.com/Elaina-liang/AI-Data-Analyst](https://github.com/Elaina-liang/AI-Data-Analyst)

---

**项目状态：持续开发中**

本项目主要用于 Python 数据分析、大数据技术及 AI 应用开发的学习与实践。
