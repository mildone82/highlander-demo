# 检索评测

`dataset.jsonl` 是离线检索评测集（question + relevant chunk ids）。`evaluate.py`
默认使用确定性 hashing embedder + 内存向量库计算 `recall@k` 与 `precision@k`，
无需 AWS/GPU。

```bash
python eval/evaluate.py --top-k 4
```

生产评测设置 `VECTOR_STORE_PROVIDER=s3_vectors`（并配置 `EMBEDDER_*`/`VECTOR_*`
环境变量）即可切换到 `OpenAICompatibleEmbedder` / `S3VectorsStore`，接口一致。
建议在实际知识库上建立 50+ 条黄金问答对，并在 CI/监控中持续追踪 recall 与
precision（阶段 2 的演进触发条件）。
