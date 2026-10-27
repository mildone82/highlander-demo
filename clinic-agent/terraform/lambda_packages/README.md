# Lambda 代码包

`terraform apply` 前，在此目录放置以下 zip（每个 zip 根目录须含入口文件）：

| 文件 | 运行时入口 | 职责 |
|---|---|---|
| `authorizer.zip` | `index.handler` | 校验 JWT 签名/issuer/audience/expiry/scope，返回 IAM policy |
| `api_handler.zip` | `index.handler` | API 业务逻辑：查询 client 资料、触发 AgentCore 会话、报表任务投递 |
| `model_gateway.zip` | `index.handler` | DeepSeek OpenAI 兼容封装：超时/重试/熔断/降级/去标识化/审计 |
| `report_generator.zip` | `index.handler` | 渲染 HTML 报表（与 `report_generator/` 模块同源）并写 S3 |
| `ingest.zip` | `index.handler` | S3 事件 → 分块 → embedding → 写 S3 Vectors + DynamoDB 元数据 |

示例构建命令（以 report_generator 为例，将模板目录一并打进包内）：

```bash
cd ../../report_generator
pip install -r requirements.txt -t build
cp -r src build/
cp -r templates build/
cd build && zip -r ../../terraform/lambda_packages/report_generator.zip .
```

说明：`filename` 指向不存在的 zip 时 `terraform validate` 仍会通过（validate 不读取文件内容），但 `apply` 需要真实文件。
