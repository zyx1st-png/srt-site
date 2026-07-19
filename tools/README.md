# 站点共享内容维护

主导航只有一个来源：`tools/sync_shared.py` 里的 `GROUPS`。页面中的导航是构建产物，不要直接逐页编辑。

修改导航后，在仓库根目录运行：

```bash
python3 tools/sync_shared.py
python3 tools/build_search_index.py
python3 tools/build_sitemap.py
python3 tools/check_site.py
```

`check_site.py` 会逐页比较导航块与唯一来源；任何旧版或相对路径错误都会使检查失败。发布前必须通过该检查。

## 视频批处理工作流

视频栏目由 `tools/video_catalog.json` 统一管理。以后不要手工复制视频详情页、列表卡片或导航链接。

### 1. 登记集数

在 catalog 中新增一集，初始使用：

- `status: "draft"`
- `subtitle_status: "draft"`
- `source_file` 只写 `Downloads/SRT video` 中的原始 NotebookLM 视频文件名
- `output`、`poster`、`subtitle` 使用新的唯一文件名

### 2. 识别与大模型精修

```bash
python3 tools/video_pipeline.py prepare --episodes Q03,Q04
```

命令会在 `tools/video_work/Qxx/` 生成原声转写和 `REFINEMENT.md`。大模型必须结合当前书稿逐句精修，保留时间码，把批准稿写入 catalog 指定的字幕路径，然后把 `subtitle_status` 改为 `approved`。

NotebookLM 原声默认按英文识别；若某一集确为中文原声，追加 `--language Chinese`。

禁止把自动翻译稿直接发布。重点检查专名、SRT 术语、上下文语义和中文断句。

### 3. 时间轴与文字质量门

```bash
python3 tools/video_pipeline.py audit
```

检查包括：序号、负时长、字幕重叠、单条时长、长度和已知机翻错误词。检查失败时禁止烧录。

### 4. 从原始视频生成成品

```bash
python3 tools/video_pipeline.py render --episodes Q03,Q04
```

流水线只接受站点仓库之外的原始视频，拒绝以 `assets/media` 中的成品作为输入，从流程上避免字幕被二次烧录。它会生成视频、封面、三张抽查帧和包含源文件哈希的构建记录。

### 5. 生成页面并完成全站检查

把通过验收的集数改成 `status: "published"`，运行：

```bash
python3 tools/video_pipeline.py publish
```

该命令统一更新视频列表、详情页、主导航、搜索索引和 sitemap，并执行全站检查。完整单集操作也可用：

```bash
python3 tools/video_pipeline.py run --episodes Q03
```

### 发布硬规则

- 原始视频永远只从 `Downloads/SRT video` 读取，不复制进仓库。
- 成品视频只能由原始视频加“已批准字幕”生成一次。
- SRT 时间轴必须零重叠。
- 页面播放器不增加第二条字幕轨道。
- 每集发布前检查开头、中段、结尾三张抽查帧。
- catalog 是集数、文件名、页面和导航的唯一来源。
