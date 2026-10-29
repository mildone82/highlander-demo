# 中国区诊所服务 Agent — Stage 3 交付

本目录包含 Stage 3（实现阶段）的两项交付：

- `terraform/` — 覆盖 Stage 2 架构全部 AWS 资源的模块化 Terraform 骨架，可直接部署到 `cn-north-1`。
- `report_generator/` — 三风格 × 三视图的确定性 HTML 报表生成模块（Jinja2 模板 + CSS 主题），含 9 份示例渲染结果。

## 架构遵循

实现严格对齐 Stage 2 架构：Keycloak（ECS Fargate + RDS PostgreSQL）OIDC 认证、Lambda Authorizer 鉴权、API Gateway、Bedrock AgentCore Runtime 编排、S3 client 资料桶、S3 Vectors 检索、SageMaker 自托管 embedding（TEI + BGE-M3）、Model Gateway 接入 DeepSeek（OpenAI 兼容）、Report Generator 渲染、SPA/报表桶、ElastiCache Valkey、DynamoDB、SQS + EventBridge + Step Functions 异步化、第三方境内 CDN 扩展点、KMS/Secrets Manager/CloudTrail/CloudWatch。

**已核实的前置事实（对应 Stage 2 的“Stage 3 核对 provider 版本”）：**

- `aws_bedrockagentcore_agent_runtime` 自 hashicorp/aws `v6.44.0` 起可用。
- `aws_s3vectors_vector_bucket` / `aws_s3vectors_index` 自 `v6.24.0` 起可用。
- 本骨架约束 provider `>= 6.44.0`，已验证 `terraform validate` 通过（Terraform 1.17.0 + AWS provider 6.70.0）。

## 前置条件

1. AWS 中国区账号（北京 `cn-north-1`），IAM 具备创建所列资源的权限。
2. Terraform `>= 1.5`；本机验证使用 1.17.0。
3. ICP 备案主体与域名（自定义域名、API 域名、CDN 的关键路径，最先启动）。
4. 镜像入区：把 Keycloak 镜像与 TEI + BGE-M3 推理镜像推送到北京区 ECR，并回填 `keycloak_image` / `embedding_model_image`。
5. DeepSeek 企业条款与训练 opt-out 已洽签；API Key 部署后写入 Secrets Manager。
6. 第三方境内 CDN（Cloudsway / 白山云）账号，源站为 `spa_bucket` 与 `report_bucket`（经签名 URL）。

## Terraform 部署步骤

```bash
cd terraform

# 1. 准备 Lambda 代码包（见 terraform/lambda_packages/README.md）

# 2. 配置变量
cp dev.tfvars.example dev.tfvars
# 编辑 dev.tfvars：回填 ICP 域名、ACM 证书 ARN、ECR 镜像 URI

# 3. （可选）启用远程状态
cp backend.tf.example backend.tf
# 编辑 backend.tf 回填 bucket/key/dynamodb_table

# 4. 初始化与校验
terraform init
terraform validate
terraform plan -var-file=dev.tfvars

# 5. 部署
terraform apply -var-file=dev.tfvars
```

部署后需手动/脚本完成（不在纯 IaC 内）：

- 把 DeepSeek API Key 写入 `aws_secretsmanager_secret`（`<prefix>/llm/deepseek`，JSON 字段 `api_key`）。
- Keycloak 首次登录 admin 控制台，创建 realm、OIDC client 与用户；authorizer 的 issuer/audience 需与之对应。
- 配置第三方 CDN 回源 S3（`spa_bucket` / `report_bucket`）并绑定已备案域名。
- 上传 SPA 静态资源到 `spa_bucket`。

## Terraform 模块清单

| 模块 | 覆盖的架构组件 | 关键资源 |
|---|---|---|
| `network` | VPC 多 AZ、公/私/数据子网、NAT、网关/接口端点 | `aws_vpc`、`aws_subnet`、`aws_nat_gateway`、`aws_vpc_endpoint` |
| `kms` | 共享 CMK + 每诊所独立 CMK | `aws_kms_key`、`aws_kms_alias` |
| `storage` | client 资料桶、报表桶、SPA 桶、日志桶 | `aws_s3_bucket` 及加密/版本化/生命周期/公共访问阻断 |
| `vector` | S3 Vectors 向量桶 + 每诊所独立索引 | `aws_s3vectors_vector_bucket`、`aws_s3vectors_index` |
| `auth` | Keycloak OIDC（ALB + ECS Fargate + RDS PG） | `aws_ecs_service`、`aws_lb`、`aws_db_instance` |
| `api` | API Gateway + Lambda Authorizer | `aws_api_gateway_rest_api`、`aws_lambda_function` |
| `compute` | AgentCore Runtime、SageMaker embedding、4 个 Lambda | `aws_bedrockagentcore_agent_runtime`、`aws_sagemaker_endpoint`、`aws_lambda_function` |
| `state` | DynamoDB 表 + ElastiCache Valkey | `aws_dynamodb_table`、`aws_elasticache_serverless_cache` |
| `async` | 长报表异步化 | `aws_sqs_queue`、`aws_sfn_state_machine`、`aws_cloudwatch_event_rule` |
| `security` | WAFv2 | `aws_wafv2_web_acl` |
| `observability` | CloudWatch 日志/告警 + CloudTrail | `aws_cloudwatch_log_group`、`aws_cloudwatch_metric_alarm`、`aws_cloudtrail` |

## 报表生成模块

使用与实现方案见 `report_generator/README.md`。示例输出在 `report_generator/examples/output/`：

- `elegant-*` 典雅风、`cool-*` 酷炫风、`realistic-*` 写实风；
- 每种风格含 `summary`（摘要）、`full`（全报告）、`comparison`（分阶段对比）三视图。

## 验证情况

- `terraform validate` 通过（Terraform 1.17.0，AWS provider 6.70.0，无错误无告警）。
- `terraform plan` 未执行：环境无 AWS 凭据；语法与 schema 已由 `validate` 覆盖。
- 报表生成器本地运行通过，9 份示例 HTML 已渲染。

## 设计缺口 / 待确认（未改动设计，仅回帖提示）

1. 第三方 CDN 无 AWS 原生 Terraform 资源，本骨架以 `spa_bucket` / `report_bucket` 作为回源站输出，CDN 侧需用第三方 provider 或手工配置。
2. SageMaker 与 Keycloak 的境内镜像（ECR 镜像源、Serverless 配额）需在部署前落实，已参数化。
3. AgentCore Runtime 与 S3 Vectors 为新服务，配额/SLA 需实测；Lambda 的 IAM 策略为骨架级，正式上线应按最小权限进一步收紧。
