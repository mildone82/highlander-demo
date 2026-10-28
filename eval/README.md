# 检索评测

`dataset.jsonl` 是离线检索评测集（question + relevant chunk ids）。`evaluate.py`
使用确定性 hashing embedder + 内存向量库计算 `recall@k`，无需 AWS/GPU。

```bash
python eval/evaluate.py --top-k 4
```

生产评测只需把 `evaluate.py` 里的 `LocalHashingEmbedder` / `InMemoryVectorStore`
替换为 `OpenAICompatibleEmbedder` / `S3VectorsStore`（接口一致）。建议在实际
知识库上建立 50+ 条黄金问答对，并监控 recall/precision（阶段 2 的演进触发条件）。
