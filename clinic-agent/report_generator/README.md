# HTML 报表生成模块（三风格 × 三视图）

确定性渲染方案：LLM 只产出“内容与结构”（摘要、叙事、对比结论，结构化 JSON/Markdown 片段），Jinja2（autoescape 开启）负责“排版与安全”，CSS 主题变量负责“风格切换”。**绝不直接渲染 LLM 直出的 HTML**，从源头规避 XSS 与布局漂移。影像以 `<figure>` / 时间轴画廊呈现，原图走短时签名 URL，无图时渲染占位块。

## 风格与视图

- 风格：`elegant` 典雅、`cool` 酷炫、`realistic` 写实，三套主题共享同一语义化骨架，新增风格只需加一份 CSS。
- 视图：`summary` 摘要、`full` 全报告、`comparison` 分阶段对比。

## 使用

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m reportgen \
  --data examples/sample_data.json \
  --style elegant --view full \
  --out /tmp/elegant-full.html
```

或程序化调用：

```python
from pathlib import Path
from reportgen import ReportRenderer, ReportData

renderer = ReportRenderer(Path("templates"))
html = renderer.render(data, style="cool", view="comparison")
renderer.render_to_file(data, "cool", "comparison", Path("out.html"))
```

## 结构

- `src/reportgen/models.py` — 数据模型（Client / Metric / Record / Stage / ReportData）。
- `src/reportgen/views.py` — 三视图的上下文构建。
- `src/reportgen/renderer.py` — Jinja2 渲染器与主题/视图选择。
- `templates/base.html.j2` — 语义化骨架，内联所选主题 CSS（输出为单文件 HTML，可离线直接打开）。
- `templates/themes/*.css` — 三套主题。
- `templates/views/*.html.j2` — 三视图模板。

## 与 Lambda 的关系

`report_generator.zip`（`terraform/lambda_packages/`）与本品同源：把 `src/` 与 `templates/` 打包进 zip，handler 调 `ReportRenderer.render_to_file` 后上传到报表桶。分阶段对比依赖 `recorded_at` 数值时间戳做 S3 Vectors 范围过滤，写入侧必须带该元数据。

## 示例

`examples/generate_samples.py` 渲染全部 9 种组合到 `examples/output/`，可直接在浏览器打开验证三种风格差异。
