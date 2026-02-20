# Space Bio Agent - 多智能体评估系统

基于 FastAPI 的多智能体系统，用于评估空间科学研究课题。系统使用 5 类专家智能体提供综合评估，包含维度评分和学术文献背景信息。

## 项目结构

```
space-bio-agent/
├── agents/                  # 智能体模块
│   ├── base_agent.py        # 基础智能体类
│   ├── science_project_manager.py
│   ├── engineer.py
│   ├── researcher.py
│   ├── astronaut.py
│   └── sociologist.py
├── config.py                # 配置文件
├── llm_client.py            # LLM API 客户端
├── literature_search.py     # 学术文献背景信息模块
├── multi_agent_system.py    # 多智能体协调系统
├── web_service.py           # FastAPI Web 服务
└── requirements.txt         # 依赖
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.py` 进行配置：

```python
# LLM API 配置
API_URL = "https://api.openai.com/v1/chat/completions"
LLM_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_KEY = "your_openai_api_key"

# CORE 学术文献 API（可选）
CORE_API_KEY = "your_core_api_key"  # 从 https://core.ac.uk/services/api 获取
CORE_API_BASE_URL = "https://api.core.ac.uk/v3"

# 文献背景功能开关
ENABLE_LITERATURE_BACKGROUND = True  # 设为 False 禁用
```

## 运行服务

### 开发环境
```bash
uvicorn web_service:app --host 0.0.0.0 --port 8000
```

### 生产环境（后台运行）
```bash
nohup uvicorn web_service:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

## API 端点

### POST /evaluate

使用 5 类专家智能体评估空间科学研究课题。

**请求：**
```json
{
  "topic": "Study of bone density loss mechanisms in microgravity and protective strategies",
  "use_literature_background": true
}
```

**响应：**
```json
{
  "agent_scores": {
    "researcher": {
      "agent_role": "researcher",
      "analysis": "...",
      "score": 9.0,
      "dimension_scores": {
        "SCIENTIFIC SIGNIFICANCE": 9,
        "RESEARCH METHODOLOGY": 8,
        "NOVELTY AND INNOVATION": 8,
        "SPACE-SPECIFIC NECESSITY": 10,
        "SCIENTIFIC IMPACT": 9
      },
      "background_context_used": true
    },
    "engineer": {
      "agent_role": "engineer",
      "score": 7.0,
      "dimension_scores": {
        "TECHNICAL FEASIBILITY": 7,
        "SYSTEM INTEGRATION": 6,
        "SPACE ENVIRONMENT CONSIDERATIONS": 8,
        "HARDWARE AND INSTRUMENTATION": 7,
        "OPERATIONAL COMPLEXITY": 6,
        "ENGINEERING VALUE": 8
      }
    }
  },
  "weighted_total_score": 7.61,
  "literature_background": {
    "entities": ["Microgravity Environment", "Bone Density Loss", "Protective Strategies"],
    "entity_backgrounds": {
      "Bone Density Loss": {
        "background": {
          "definition": "Bone density loss refers to the reduction in mineral content and structural integrity of bone tissue...",
          "progress": "Significant advancements have been made in understanding the mechanisms underlying bone density loss...",
          "challenges": "Key issues include the complexity of replicating microgravity conditions..."
        },
        "literature_count": 5,
        "literature_references": [
          {
            "title": "Changes in mineral metabolism with immobilization/space flight",
            "authors": ["Gallagher, J. C."],
            "year": 2023,
            "doi": "10.1234/example",
            "links": [
              {"type": "doi", "url": "https://doi.org/10.1234/example"},
              {"type": "download", "url": "https://core.ac.uk/download/..."},
              {"type": "core", "url": "https://core.ac.uk/works/12345"}
            ]
          }
        ]
      }
    }
  }
}
```

## 功能特性

### 1. 五类专家智能体

| 智能体 | 评估维度 |
|--------|----------|
| **Researcher** | 科学意义、研究方法、创新性、太空必要性、科学影响 |
| **Engineer** | 技术可行性、系统集成、硬件设备、操作复杂度 |
| **Astronaut** | 操作可行性、乘员安全、人因工程、太空环境 |
| **Science Project Manager** | 项目可行性、资源需求、风险评估、战略价值、利益相关者 |
| **Sociologist** | 社会相关性、伦理考量、公平正义、公众参与、技术转化 |

### 2. 维度评分

每个智能体对其评估的各个维度分别打分（1-10分），并给出总分。

### 3. 学术文献背景信息

评估前，系统自动执行：
1. **提取关键实体**：使用 LLM 识别 2-3 个关键科学概念
2. **搜索文献**：通过 CORE API 搜索相关学术论文
3. **综合背景**：生成定义、研究进展和挑战
4. **共享上下文**：5 类专家使用相同的背景信息

### 4. 引文链接

每篇文献引用包含多种链接类型：
- `doi`: DOI 链接（如 https://doi.org/10.1234/...）
- `download`: CORE 直接下载 PDF
- `fulltext`: 全文来源链接
- `core`: CORE 平台页面

## 测试

```bash
# 基本评估
curl -X POST "http://localhost:8000/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"topic": "Effects of long-duration spaceflight on human cardiovascular system"}'

# 禁用文献背景
curl -X POST "http://localhost:8000/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"topic": "Mars soil analysis for astrobiology", "use_literature_background": false}'

# 查看 API 文档
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## 智能体权重

此处由于为线上服务，为了节省token，采用的是每类角色一个个体，打分后进行加权结合给出总分的方法。论文中所用的“评审团”策略是在高算力机器上进行的。

加权总分计算权重：

| 智能体 | 权重 |
|--------|------|
| Sociologist | 0.41 |
| Researcher | 0.37 |
| Science Project Manager | 0.13 |
| Engineer | 0.05 |
| Astronaut | 0.04 |

## 注意事项

1. 确保在 `config.py` 中正确配置 LLM API 凭证
2. CORE API Key 为可选项；未设置时使用模拟数据
3. 在配置中设置 `ENABLE_LITERATURE_BACKGROUND = False` 可禁用文献搜索
4. CORS 设置可在 `web_service.py` 中修改
