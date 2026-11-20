# 深度登记 · 扶梯停运统计簿

- 规模：中型
- 核心规则：按设备对营业窗口内的事件端点扫线，先裁决事件原因，再按审批覆盖重切停运片段。
- 工作流：站点值班员对平夜班时长后，核对异常片段并保存接班证据。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 设备班表 | 核对跨日班次及营业并集 | `GET /api/schedules/{sample}` | `app/modules/schedules/calendar.py` | `tests/test_schedules.py` |
| M2 故障事件 | 找出重传、冲突、坏行与未恢复报码 | `GET /api/events/{sample}` | `app/modules/events/ledger.py` | `tests/test_events.py` |
| M3 时段裁切 | 查原报码落在营业内外的时长 | `GET /api/clipping/{sample}` | `app/modules/clipping/cut.py` | `tests/test_clipping.py` |
| M4 原因归属 | 查看交叠事件的归属行与候选行 | `GET /api/attribution/{sample}` | `app/modules/attribution/sweep.py` | `tests/test_attribution.py` |
| M5 豁免计入 | 核对确实适用的审批及覆盖秒数 | `GET /api/exemptions/{sample}` | `app/modules/exemptions/register.py` `app/modules/exemptions/apply.py` | `tests/test_exemptions.py` |
| M6 可用率核对 | 逐台核对四类秒数、差额和可用率 | `GET /api/reconcile/{sample}` | `app/modules/reconcile/balance.py` | `tests/test_reconcile.py` |
| M7 班报归档 | 保存班报、查询证据、重跑和下载 | `POST /api/runs` | `app/modules/reports/store.py` `app/modules/reports/manifest.py` `app/modules/reports/evidence.py` | `tests/test_reports.py` |

## 陷阱登记

| TRAP | 现象与样例 | 朴素实现会怎样 | 本项目处理 | 处理位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-07 | `dirty/events.json` 第 3 行未恢复 | 直接记为零或全段停运 | 空恢复时刻使营业内有效片段带缺证原因 | `app/modules/events/ledger.py` | `tests/test_events.py::test_null_close_marked_unknown` |
| TRAP-08 | 两份 `devices.json` 含设备 `001` | 转整数会丢掉设备号前导零 | 设备号按文本参与关联 | `app/modules/schedules/calendar.py` | `tests/test_schedules.py::test_device_preserves_leading_zero` |
| TRAP-11 | `dirty/events.json` 第 2、6 行使用不同偏移 | 同一停运被当成两条 | 整秒归一后认作重传 | `app/modules/events/ledger.py` | `tests/test_events.py::test_timezone_equivalent_duplicate` |
| TRAP-13 | `dirty/events.json` 第 5 行晚于较晚发生的第 4 行到达 | 跳过迟到记录 | 采信后按开始时刻排序并保留原行号 | `app/modules/events/ledger.py` | `tests/test_events.py::test_out_of_order_records_retained` |
| TRAP-14 | `dirty/events.json` 第 8、9 行同报码异时段 | 后写覆盖，遗漏争议时长 | 两行隔离且保留可计算的争议窗口 | `app/modules/events/ledger.py` | `tests/test_events.py::test_conflicting_report_codes_quarantined` |
| TRAP-19 | `dirty/events.json` 第 2、5 行原因交叠 | 随顺序改写归属或叠加时长 | 安全联锁优先，保留机械故障来源 | `app/modules/attribution/sweep.py` | `tests/test_attribution.py::test_higher_priority_wins_without_erasing_loser` |
| TRAP-21 | `dirty/shifts.json` 第 5 行引用未登记设备 | 凭空增加营业窗口 | 隔离缺设备引用的班次 | `app/modules/schedules/calendar.py` | `tests/test_schedules.py::test_unknown_device_shift` |
| TRAP-23 | `clean/shifts.json` 第 1 行结束时刻跨入次日 | 午夜后营业漏计 | 按次日端点展开，右端排除 | `app/modules/schedules/calendar.py` | `tests/test_schedules.py::test_midnight_shift` |
| TRAP-25 | `dirty/shifts.json` 第 1、3 行交叠半小时 | 双计营业秒 | 保留原班次并计算并集 | `app/modules/schedules/calendar.py` | `tests/test_schedules.py::test_overlapping_shifts_are_unioned` |

## 联合回归

- 审批重叠保留双份审批证据，同时避免重复计秒。见 `tests/test_exemptions.py::test_overlapping_approvals_count_once`。
- 已隔离、已采信和重传行数对平输入。见 `tests/test_events.py::test_event_counts_conserve`。
- 每台设备的四类秒数对平营业并集，片段连续。见 `tests/test_reconcile.py::test_per_device_conservation_and_contiguity`。
- 并发保存只写一份 SQLite 记录。见 `tests/test_reports.py::test_duplicate_posts_commit_once`。
