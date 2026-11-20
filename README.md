# 扶梯停运统计簿

值班员按设备和营业窗口核对停运时间。首页载入异常夜班，显示营业、可用、责任停运、豁免和缺证秒数。选中时间线片段即可追溯归属报码、重传、审批单和班表。

```sh
docker compose up --build
```

打开 [统计工作台](http://localhost:18444/) 或 [接口说明](http://localhost:18444/docs)。右上角可切换干净和异常样例，也可导入一份班报 JSON。导入自动归档。内置样例点击「保存班报」归档，归档页可重算、下载原始输入与计算证据。

## 示例与规则

- [干净样例](sample_data/clean/)营业 28,800 秒，确认可用率 86.67%。
- [异常样例](sample_data/dirty/)营业 36,000 秒，含缺证 5,400 秒，可用率下限 42.86%。
- 自备数据时，把样例的 `window.json` 和四份数组组装成一个对象，字段名见[数据字典](docs/DATA-DICTIONARY.md)。
- [模块与回归登记](docs/DEPTH.md)列出每条规则的处理位置和测试。

## 验证

```sh
docker compose config --quiet
docker compose exec -T app pytest -q
```

宿主运行可使用 `python -m pip install -r requirements.txt` 后执行 `python -m pytest -q`。数据库默认写入 `instance/reports.sqlite`。容器使用命名卷 `reports` 保存班报，同一卷可在服务重启后继续读取。需要独立数据库时，可用新的 Compose 项目名启动。
