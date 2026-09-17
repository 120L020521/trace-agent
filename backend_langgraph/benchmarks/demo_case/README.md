# 稳定演示案例：北京三日行程与闭馆重规划

该案例用于在面试或项目演示中稳定展示完整链路：

1. 同时上传 Markdown 约束资料和 PNG 约束卡，展示多模态资料摄取；
2. Evidence Router 根据资料规模选择上下文策略；
3. 多 Agent 调用实时地图和天气工具；
4. CP-SAT 排程并由 Validation Engine 校验；
5. 自动选择第二天的首个景点，注入“临时闭馆”事件；
6. 验证 Revision 递增、闭馆景点移除、其他日期保持不变以及新 Trace 生成。

脚本使用“当前日期后 7 天”作为出发日期，避免固定日期过期；闭馆目标从初始结果动态选择，避免依赖模型必须生成某个特定景点。

## 运行

先启动后端，然后执行：

```powershell
cd D:\codes\Multi-agent-trip-planner-main\backend_langgraph
python benchmarks\demo_case\run_demo.py
```

默认会上传 `beijing_material.md` 与 `../fixtures/beijing_constraint_card.png`。如果当前模型不支持视觉输入，可使用纯文本兼容模式：

```powershell
python benchmarks\demo_case\run_demo.py --skip-image
```

结果保存在 `benchmarks/demo_case/demo_output.json`。`passed=true` 表示六项自动验收全部通过。

## 推荐演示顺序

- 在工作台创建同样的北京三日任务，同时上传 `beijing_material.md` 和图片约束卡；
- 展示 Evidence Router 的策略、覆盖率和引用；
- 展示 CP-SAT 状态与 Validation Report；
- 点击“干预重规划”，模拟任一景点闭馆；
- 打开版本历史，对比 v0 与 v1；
- 打开链路穿刺，说明新旧 Trace 和受影响日期；
- 最后展示数据飞轮中的反馈和难例候选。
