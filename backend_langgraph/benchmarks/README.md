# TripPilot 20-Case Benchmark

`benchmark_20.jsonl` 包含 20 条规划与动态恢复任务，用于评估 Agent Runtime，而不是只评价最终文本是否流畅。

其中 5 条任务会上传真实 PNG 文件，覆盖车票识别、酒店订单识别、场馆预约冲突、天气预警和图文来源冲突。图片均为字段可控的合成测试资料，不含真实个人信息；源文件和可复现生成脚本位于 `fixtures/`。

## 覆盖分布

| 类别 | 数量 | 主要检查 |
|---|---:|---|
| 普通旅行规划 | 3 | 日期、景点强度、三餐和基础可行性 |
| 预算限制 | 3 | 总费用不超过预算、每日景点数 |
| 营业时间冲突 | 2 | CP-SAT 可行性及开放时间人工复核 |
| 无障碍或饮食要求 | 3 | 硬约束通过及内容级人工复核 |
| 证据缺失 | 2 | Evidence Router 充分性与错误引用 |
| 来源冲突 | 2 | 多来源引用和冲突处理人工复核 |
| 景点闭馆 | 2 | 目标移除、Revision、未影响日期稳定性 |
| 天气变化 | 2 | 局部重规划和未影响日期稳定性 |
| 交通延误 | 1 | 延误后的重新排程和求解可行性 |

## 多模态测试资料

| 图片 | 用途 |
|---|---|
| `railway_ticket.png` | 提取车次、日期、时间、席位和票价 |
| `hotel_order.png` | 提取入住区间、金额、取消规则和饮食备注 |
| `museum_reservation.png` | 识别预约时段与“周一闭馆”的内部冲突 |
| `weather_alert.png` | 识别预警时段、影响区域和停运信息 |
| `beijing_constraint_card.png` | 稳定演示中的图片约束输入 |

重新生成图片：

```powershell
python benchmarks\fixtures\generate_image_fixtures.py
```

图片任务需要后端配置支持视觉输入的模型。Runner 会保留这些任务的自动化结构断言，同时把 OCR 字段正确性、冲突解释和引用完整性列为人工复核项，避免仅凭接口成功就判定多模态理解通过。

## 运行方式

先启动后端，再执行：

```powershell
cd D:\codes\Multi-agent-trip-planner-main\backend_langgraph
python benchmarks\evaluate_benchmark_20.py
```

指定服务地址或输出位置：

```powershell
python benchmarks\evaluate_benchmark_20.py `
  --base-url http://localhost:8000 `
  --output benchmarks\benchmark_20_results.json
```

Runner 会自动完成资料上传、规划、动态目标解析和重规划，并输出：

- 自动化通过率；
- 平均端到端延迟；
- 分类数量和状态数量；
- 每条断言的实际值；
- Trace ID 和实际注入的扰动；
- 需要人工复核的语义断言。

`passed_pending_manual` 表示结构化断言已通过，但无障碍、饮食、营业时间或来源冲突等内容仍需人工确认。不要把这类任务直接计作最终通过率；建议人工审核后再生成正式实验指标。

## 稳定演示

完整演示材料位于 `demo_case/`：

```powershell
python benchmarks\demo_case\run_demo.py
```

脚本自动使用当前日期后 7 天，并从第二天的实际规划结果中选择闭馆目标，因此不依赖固定日期或模型必须输出某个景点。
