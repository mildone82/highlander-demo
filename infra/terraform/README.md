# Terraform（IaC）

按阶段 2 设计拆分为 `network / inference / storage / compute / observability`
五个模块，部署目标分区为 `cn-north-1`（aws-cn 分区，不使用全球服务）。

## 使用

```bash
cp backend.tf.example backend.tf      # 按需填写远端 state
cp dev.tfvars.example dev.tfvars     # 填写 ECR 镜像与 SageMaker 制品
terraform init
terraform plan  -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

## 需要注意的中国区差异

- 分区 ARN 为 `aws-cn`，`aws_region` 默认 `cn-north-1`。
- 中国区无 Bedrock，推理走 SageMaker 实时端点（`inference` 模块），
  模型容器镜像与 `model_data` 需提前构建并上传到 S3/ECR。
- S3 Vectors 目前 Terraform AWS provider 尚无原生资源，向量桶与索引由
  一次性脚本 `scripts/provision_s3_vectors.py` 创建（见 README 部署步骤）。
- 首次 `apply` 前建议先创建远端 state 桶与 DynamoDB 锁表。
- 内部 ALB 的客户端入口走 HTTPS:443（`alb_certificate_arn` 指向 `cn-north-1`
  的 ACM 证书）；VPC 内服务间调用走 HTTP:80 私有监听器。`model_api_key_primary/
  fallback` 为空时 Terraform 会直接报错（fail closed），避免以占位密钥部署。
- `compute` 模块除 `rag/memory/model_gateway` 外，还部署 LangGraph 回退
  `agent` 服务（`/ask`）、`memory_worker`（消费 memory SQS，异步写记忆）与
  `ingestion_worker`（消费 ingestion SQS，解析/分块/向量化入库）。
