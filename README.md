# highlander-demo：AWS 中国区知识助手

按 HIG-9 阶段 2 架构设计实现的知识助手工程（阶段 3）。基线技术组合：
**AgentCore（Runtime/Gateway/Identity）+ 自托管 mem0 + S3 Vectors（直连 API）+
区内自托管推理（Qwen/DeepSeek + BGE-M3）**，国内已备案模型 API 作为降级。

## 组件与目录

| 目录 | 职责 |
| --- | --- |
| `agent/` | Agent 编排：AgentCore Runtime 定义与工具注册（`agentcore_main.py`）、LangGraph 回退（`langgraph_main.py`）、共享主流程（`orchestrator.py`） |
| `services/agent/` | LangGraph 回退的 HTTP 服务（`POST /ask`），是当前可在 ECS 上真实部署的路径 |
| `services/rag/` | `POST /retrieve`：query 向量化 + S3 Vectors 检索 |
| `services/memory/` | mem0 封装，`search/add/update/delete` 四契约，适配 S3 Vectors + SQLite 历史；`worker.py` 异步消费 memory SQS |
| `services/model_gateway/` | OpenAI 兼容推理路由：区内端点主、国内 API 降级 + 限流/熔断 |
| `ingestion/` | S3→SQS→Worker：解析/分块/向量化/入库 + DynamoDB 幂等 |
| `infra/terraform/` | Terraform：`network/inference/storage/compute/observability` 五模块 |
| `eval/` | 离线检索评测集与 recall@k 脚本 |
| `app/` | 共享基础：向量库抽象（S3 Vectors / 内存）、LLM/Embedder（OpenAI 兼容 / 本地哈希）、schema |

## 本地快速验证（无需 AWS/GPU）

```bash
python3 -m venv .venv && source .venv/bin/activate   # 需 Python 3.10+（mem0ai 2.2.1 要求）
pip install -r requirements-dev.txt

# 1) 单元/集成测试（含提问→检索→生成→记忆写入主流程）
pytest

# 2) 主流程端到端演示（确定性 fakes）
python scripts/demo_e2e.py

# 3) 检索评测（recall@k）
python eval/evaluate.py --top-k 4

# 4) 以 HTTP 方式启动三个服务（memory:8000 / rag:8001 / model-gateway:8002）
python scripts/run_local_services.py
```

本地模式默认使用内存向量库、哈希 embedder、fake LLM 与 fake 记忆，验证的是
“提问 → 检索 → 生成 → 记忆写入”的编排链路；生产行为由环境变量切换到真实实现。

## 配置

所有配置通过环境变量注入（生产环境中由 ECS task definition / Secrets Manager
提供，禁止明文写死密钥）。

### RAG 服务（`services/rag`）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `EMBEDDER_PROVIDER` | `hashing` | `openai` 或 `hashing` |
| `EMBEDDER_BASE_URL` | `http://localhost:8002/v1` | 模型网关 OpenAI 兼容地址 |
| `EMBEDDER_MODEL` | `bge-m3` | embedding 模型名 |
| `EMBEDDER_DIMS` | `64` | 向量维度（生产 1024） |
| `VECTOR_STORE_PROVIDER` | `in_memory` | `s3_vectors` 或 `in_memory` |
| `VECTOR_BUCKET` / `VECTOR_INDEX` | `knowledge-assistant-vectors` / `knowledge` | S3 Vectors 桶与索引 |
| `VECTOR_REGION` | `cn-north-1` | 区域 |

### Memory 服务（`services/memory`）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `MEMORY_PROVIDER` | `fake` | `mem0` 或 `fake` |
| `MEMORY_LLM_BASE_URL` / `MEMORY_EMBEDDER_BASE_URL` | 模型网关地址 | mem0 的 LLM/Embedder 走 OpenAI 兼容端点 |
| `MEMORY_VECTOR_BUCKET` / `MEMORY_VECTOR_INDEX` | `knowledge-assistant-vectors` / `memory` | mem0 记忆索引 |
| `MEMORY_VECTOR_DIMENSION` | `64` | BGE-M3 实际为 1024 |
| `MEMORY_HISTORY_DB` | `.local-data/mem0_history.db` | SQLite 历史库路径 |
| `MEMORY_WRITE_QUEUE_URL` | 空 | 非空时 `/memory/add` 异步写入 SQS（生产默认） |
| `MEMORY_IDEMPOTENCY_TABLE` | 空 | 非空时用 DynamoDB 表按 `request_id` 幂等去重（worker 使用） |

### 模型网关（`services/model_gateway`）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `MG_PRIMARY_BASE_URL` / `MG_FALLBACK_BASE_URL` | 空 | 区内/国内 OpenAI 兼容地址（未配置时用 fake 模式） |
| `MG_PRIMARY_API_KEY` / `MG_FALLBACK_API_KEY` | 空 | 对应 API key（配置了 URL 但 key 为空时 fail-closed 拒绝启动） |
| `MG_PRIMARY_LLM_MODEL` / `MG_PRIMARY_EMBED_MODEL` | `qwen2.5-7b-instruct` / `bge-m3` | 模型名 |

### 服务契约

- `POST /retrieve`：`{query, top_k, user_id, request_id}` → `{chunks[], latency_ms}`
- `POST /memory/search`：`{user_id, query, limit}` → `{memories[]}`
- `POST /memory/add`：`{user_id, messages[], metadata, request_id?}` → `{memory_ids[], request_id?, queued}`（配置 `MEMORY_WRITE_QUEUE_URL` 时异步入队）
- `POST /memory/update/{id}`、`DELETE /memory/{id}`
- `POST /v1/chat/completions`、`POST /v1/embeddings`（OpenAI 兼容）
- `POST /ask`：`{query, user_id, top_k, memory_limit, request_id?}` → 主流程回答（LangGraph 回退）

## 生产部署（cn-north-1）

1. 构建并推送镜像到 ECR：

   ```bash
   docker build -f Dockerfile.rag             -t <ecr>/rag:latest .
   docker build -f Dockerfile.memory          -t <ecr>/memory:latest .
   docker build -f Dockerfile.model_gateway   -t <ecr>/model-gateway:latest .
   docker build -f Dockerfile.agent           -t <ecr>/agent:latest .
   docker build -f Dockerfile.memory_worker   -t <ecr>/memory-worker:latest .
   docker build -f Dockerfile.ingestion       -t <ecr>/ingestion-worker:latest .
   docker push ...
   ```

2. 准备 SageMaker 推理容器镜像与模型制品（Qwen/DeepSeek、BGE-M3），填入
   `dev.tfvars`。

3. 应用 Terraform：

   ```bash
   cd infra/terraform
   cp backend.tf.example backend.tf
   cp dev.tfvars.example dev.tfvars
   terraform init && terraform apply -var-file=dev.tfvars
   ```

4. 一次性创建 S3 Vectors 桶与索引（Terraform provider 暂不支持该资源）：

   ```bash
   python scripts/provision_s3_vectors.py --bucket knowledge-assistant-vectors --dimension 1024 --region cn-north-1
   ```

5. 入库知识文档：上传到文档 S3 桶触发 S3→SQS→Worker；本地可用
   `python ingestion/cli.py <path>` 验证分块/向量化/入库链路。

## 与阶段 2 设计的偏差（需要知晓）

- **mem0 版本**：本仓库锁定 `mem0ai==2.2.1`（PyPI 当前最新版，2026-10-30 核对），
  与阶段 1 调研及阶段 2 设计一致。其 `s3_vectors` 适配器配置键仍为
  `vector_bucket_name/collection_name/embedding_model_dims/distance_metric/region_name`。
  mem0 2.2.1 要求 Python >=3.10，本地请使用 3.10+（镜像已用 `python:3.11-slim`）。
- **mem0 历史库**：`mem0ai 2.2.1` 的 OSS 包仅内置 SQLite 历史库（配置里唯一的历史
  存储入口是 `history_db_path`），无 PostgreSQL 后端，故 MVP 采用 SQLite（设计文档
  本就允许“MVP 先 SQLite”）。PostgreSQL/Aurora 需等待 mem0 提供该后端或自行扩展，
  多实例一致性在 Fargate 上会受 SQLite 限制，生产化前需处理（EFS 持久化或升级后端）。
- **AgentCore 实测（A1）**：AgentCore Runtime 指向自建 OpenAI 兼容端点的能力
  必须在 aws-cn 账号内实测；沙箱无法完成。本仓库已提供 Agent 定义与工具注册
  （`agent/agentcore_main.py`），若 A1 不成立，直接切换 LangGraph 回退路径。
  回退路径已实现为可部署的 `services/agent`（`POST /ask`）并在 Terraform
  `compute` 模块中作为 ECS Fargate 服务落地，因此“主路径或回退路径至少一条可
  按 IaC 部署”由回退路径满足；A1 通过后可用 AgentCore 替换同一工具契约。
- **S3 Vectors 与新版 boto3**：代码默认使用 `boto3.client("s3vectors")`，必要时
  通过 `VECTOR_ENDPOINT_URL` 显式指定端点规避 aws-cn 元数据滞后。

## 依赖说明

运行时依赖仅限设计文档明确提到的组件：`fastapi`/`uvicorn`（服务端点）、
`mem0ai`（记忆）、`boto3`（S3 Vectors/DynamoDB/SQS）、`openai`（OpenAI 兼容
客户端，mem0 本身也依赖）、`langgraph`（回退编排）。`pytest`/`httpx` 仅用于测试。
