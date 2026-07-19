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
