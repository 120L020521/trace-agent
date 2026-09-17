"""多智能体旅行规划系统 - LangGraph + MCP 架构

架构说明:
- 使用LangGraph构建工作流: start -> [attraction, weather, hotel]并行 -> planner -> end
- 三个子Agent通过create_react_agent创建,各自绑定对应MCP工具
- 主Agent(planner)无工具,负责整合三个子Agent的输出并生成结构化JSON
- MCP工具通过app.services.mcp_service适配为LangChain BaseTool
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent

from ..services.llm_service import get_llm
from ..services.mcp_service import get_mcp_tools
from ..services.constraint_engine import validate_trip_plan
from ..services.evidence_orchestrator import EvidenceOrchestrator, decision_dict
from ..services.itinerary_optimizer import optimize_itinerary
from ..services.experience_store import get_experience_store
from ..models.schemas import (
    TripRequest, TripPlan,
    Disruption, EvidenceReport, SourceCitation, ValidationReport,
)
from ..config import get_settings

# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。

**重要提示:**
你必须使用工具来搜索景点!不要自己编造景点信息!

**工作流程:**
1. 使用maps_text_search工具搜索景点(可尝试不同关键词多次搜索)
2. 整理搜索结果,返回包含景点名称、地址、类型、评分等信息的摘要

**返回格式:**
请返回搜索到的景点列表,每个景点包含名称、地址、类型/类别、评分(如有)。
"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。

**重要提示:**
你必须使用工具来查询天气!不要自己编造天气信息!

**工作流程:**
1. 使用maps_weather工具查询天气
2. 整理天气信息,返回天气预报摘要

**返回格式:**
请返回天气信息摘要,包含日期、白天/夜间天气、白天/夜间温度(纯数字,不要带°C)、风向风力。
"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和住宿偏好搜索合适的酒店。

**重要提示:**
你必须使用工具来搜索酒店!不要自己编造酒店信息!

**工作流程:**
1. 使用maps_text_search工具搜索酒店(关键词可用"酒店"、"宾馆"或具体住宿类型)
2. 整理搜索结果,返回酒店列表摘要

**返回格式:**
请返回搜索到的酒店列表,每个酒店包含名称、地址、价格范围(如有)、评分(如有)、类型。
"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息、天气信息和酒店信息,生成详细的旅行计划。

请严格按照以下JSON格式返回旅行计划:
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "opening_time": "09:00",
          "closing_time": "17:00",
          "priority_score": 80,
          "evidence_confidence": 0.9,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```

**重要提示:**
1. weather_info数组必须包含每一天的天气信息
2. 温度必须是纯数字(不要带°C等单位)
3. 每天安排2-3个景点
4. 考虑景点之间的距离和游览时间
5. 每天必须包含早中晚三餐
6. 提供实用的旅行建议
7. **必须包含预算信息**:
   - 景点门票价格(ticket_price)
   - 餐饮预估费用(estimated_cost)
   - 酒店预估费用(estimated_cost)
   - 预算汇总(budget)包含各项总费用
8. 只使用工具结果和用户资料中能够确认的事实；无法确认的坐标使用null,不得猜测
9. 严格满足用户给出的预算、每日景点数量、无障碍和饮食约束
10. 为每个景点提供opening_time、closing_time、priority_score和evidence_confidence，供约束求解器排程
"""


# ============ LangGraph State ============

class TripPlannerState(TypedDict):
    """旅行规划图状态 - 在节点间传递"""
    request: TripRequest
    attractions_data: str
    weather_data: str
    hotels_data: str
    retrieved_context: str
    retrieval_hits: List[Dict[str, Any]]
    evidence_report: Optional[EvidenceReport]
    trip_plan: Optional[TripPlan]
    validation_report: Optional[ValidationReport]
    repair_attempts: int
    trace_id: str
    error: Optional[str]


# ============ 查询构建辅助函数 ============

def _build_attraction_query(request: TripRequest) -> str:
    """构建景点搜索查询"""
    keywords = request.preferences[0] if request.preferences else "景点"
    query = f"请搜索{request.city}的{keywords}相关景点。"
    if request.free_text_input:
        query += f"\n额外要求: {request.free_text_input}"
    return query


def _build_hotel_query(request: TripRequest) -> str:
    """构建酒店搜索查询"""
    return f"请搜索{request.city}的{request.accommodation}相关酒店或宾馆。"


# ============ MultiAgentTripPlanner ============

class MultiAgentTripPlanner:
    """多智能体旅行规划系统 - LangGraph + MCP 架构"""

    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化LangGraph多智能体旅行规划系统...")

        try:
            settings = get_settings()
            self.llm = get_llm()

            # 获取MCP工具
            print("  - 加载MCP工具...")
            mcp_tools = get_mcp_tools()

            # 按功能筛选工具(通过工具名称匹配)
            text_search_tool = None
            weather_tool = None
            for tool in mcp_tools:
                if tool.name == "maps_text_search":
                    text_search_tool = tool
                elif tool.name == "maps_weather":
                    weather_tool = tool

            # 创建子Agent (ReAct Agent,自动处理Tool Calling循环)
            print("  - 创建景点搜索Agent...")
            self.attraction_agent = create_react_agent(
                model=self.llm,
                tools=[text_search_tool] if text_search_tool else [],
                prompt=ATTRACTION_AGENT_PROMPT,
                name="景点搜索专家"
            )

            print("  - 创建天气查询Agent...")
            self.weather_agent = create_react_agent(
                model=self.llm,
                tools=[weather_tool] if weather_tool else [],
                prompt=WEATHER_AGENT_PROMPT,
                name="天气查询专家"
            )

            print("  - 创建酒店推荐Agent...")
            self.hotel_agent = create_react_agent(
                model=self.llm,
                tools=[text_search_tool] if text_search_tool else [],
                prompt=HOTEL_AGENT_PROMPT,
                name="酒店推荐专家"
            )

            # 创建主行程规划Agent (不需要工具,纯整合)
            print("  - 创建行程规划Agent...")
            self.planner_agent = create_react_agent(
                model=self.llm,
                tools=[],
                prompt=PLANNER_AGENT_PROMPT,
                name="行程规划专家"
            )

            # 构建LangGraph工作流
            print("  - 构建LangGraph工作流...")
            self.graph = self._build_graph()

            print(f"✅ LangGraph多智能体系统初始化成功")
            print(f"   景点搜索Agent: {1 if text_search_tool else 0} 个工具")
            print(f"   天气查询Agent: {1 if weather_tool else 0} 个工具")
            print(f"   酒店推荐Agent: {1 if text_search_tool else 0} 个工具")

        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def _build_graph(self) -> StateGraph:
        """构建LangGraph状态图

        工作流:
        START -> start_node -> [attraction_node, weather_node, hotel_node] 并行
        -> planner_node (等待三个节点全部完成) -> END
        """
        builder = StateGraph(TripPlannerState)

        # 添加节点
        builder.add_node("start", self._start_node)
        builder.add_node("retrieve", self._retrieve_node)
        builder.add_node("attraction", self._attraction_node)
        builder.add_node("weather", self._weather_node)
        builder.add_node("hotel", self._hotel_node)
        builder.add_node("planner", self._planner_node)
        builder.add_node("optimize", self._optimize_node)
        builder.add_node("validate", self._validate_node)
        builder.add_node("repair", self._repair_node)

        # 设置入口
        builder.set_entry_point("start")

        builder.add_edge("start", "retrieve")

        # 检索用户资料后，并行分发到三个领域 Agent
        builder.add_conditional_edges(
            "retrieve",
            lambda state: ["attraction", "weather", "hotel"],
            ["attraction", "weather", "hotel"]
        )

        # 三个子Agent完成后汇聚到主Agent(planner)
        # LangGraph会自动等待所有入边节点完成后才执行planner
        builder.add_edge("attraction", "planner")
        builder.add_edge("weather", "planner")
        builder.add_edge("hotel", "planner")

        builder.add_edge("planner", "optimize")
        builder.add_edge("optimize", "validate")
        builder.add_conditional_edges(
            "validate",
            self._next_after_validation,
            {"repair": "repair", "end": END},
        )
        builder.add_edge("repair", "optimize")

        return builder.compile()

    def _start_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """起始节点 - 打印请求信息并初始化状态"""
        request = state["request"]
        print(f"\n{'='*60}")
        print(f"🚀 开始LangGraph多智能体协作规划旅行...")
        print(f"目的地: {request.city}")
        print(f"日期: {request.start_date} 至 {request.end_date}")
        print(f"天数: {request.travel_days}天")
        print(f"偏好: {', '.join(request.preferences) if request.preferences else '无'}")
        print(f"{'='*60}\n")
        self._record(
            state["trace_id"],
            "start",
            "request_received",
            {
                "city": request.city,
                "travel_days": request.travel_days,
                "preference_count": len(request.preferences),
                "source_count": len(request.knowledge_source_ids),
                "learning_consent": request.enable_experience_learning,
            },
        )
        return {
            "attractions_data": "",
            "weather_data": "",
            "hotels_data": "",
            "retrieved_context": "",
            "retrieval_hits": [],
            "evidence_report": None,
            "validation_report": None,
            "repair_attempts": 0,
            "trace_id": state.get("trace_id") or uuid.uuid4().hex,
            "error": None,
        }

    def _retrieve_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """路由工具、长上下文或混合检索，并验证上下文是否充分。"""
        request = state["request"]
        bundle = EvidenceOrchestrator().collect(request)
        report_payload = decision_dict(bundle)
        self._record(
            state["trace_id"],
            "retrieve",
            "evidence_routing_completed",
            {
                **report_payload,
                "hits": [
                    {
                        "source_id": hit.source_id,
                        "chunk_id": hit.chunk_id,
                        "score": hit.score,
                        "lexical_rank": hit.lexical_rank,
                        "semantic_rank": hit.semantic_rank,
                    }
                    for hit in bundle.hits
                ],
            },
        )
        if not bundle.decision.sufficient:
            self._record(
                state["trace_id"],
                "retrieve",
                "insufficient_context_detected",
                {"missing_aspects": bundle.decision.missing_aspects, "fallback_used": bundle.decision.fallback_used},
            )
        return {
            "retrieved_context": bundle.context,
            "retrieval_hits": [hit.__dict__ for hit in bundle.hits],
            "evidence_report": EvidenceReport(**report_payload),
        }

    def _attraction_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """景点搜索Agent节点 - 并行执行"""
        print("📍 子Agent [景点搜索] 开始工作...")
        request = state["request"]
        query = _build_attraction_query(request)

        result = self.attraction_agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        content = result["messages"][-1].content
        self._record(state["trace_id"], "attraction", "agent_completed", {"output_chars": len(str(content))})
        print(f"景点搜索结果: {content[:200]}...\n")
        return {"attractions_data": content}

    def _weather_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """天气查询Agent节点 - 并行执行"""
        print("🌤️  子Agent [天气查询] 开始工作...")
        request = state["request"]
        query = f"请查询{request.city}的天气信息"

        result = self.weather_agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        content = result["messages"][-1].content
        self._record(state["trace_id"], "weather", "agent_completed", {"output_chars": len(str(content))})
        print(f"天气查询结果: {content[:200]}...\n")
        return {"weather_data": content}

    def _hotel_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """酒店推荐Agent节点 - 并行执行"""
        print("🏨 子Agent [酒店推荐] 开始工作...")
        request = state["request"]
        query = _build_hotel_query(request)

        result = self.hotel_agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        content = result["messages"][-1].content
        self._record(state["trace_id"], "hotel", "agent_completed", {"output_chars": len(str(content))})
        print(f"酒店搜索结果: {content[:200]}...\n")
        return {"hotels_data": content}

    def _planner_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """主行程规划Agent节点 - 整合三个子Agent的结果"""
        print("📋 主Agent [行程规划] 开始整合信息...")
        request = state["request"]

        query = self._build_planner_query(
            request,
            state["attractions_data"],
            state["weather_data"],
            state["hotels_data"],
            state["retrieved_context"],
        )

        result = self.planner_agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        response = result["messages"][-1].content
        print(f"行程规划结果: {response[:300]}...\n")

        # 解析JSON为TripPlan对象
        trip_plan = self._parse_response(response, request)

        citations = [
            SourceCitation(
                source_id=hit["source_id"],
                source_name=hit["source_name"],
                chunk_id=hit["chunk_id"],
                excerpt=hit["text"][:240],
                score=hit["score"],
                retrieval_strategy=state["evidence_report"].strategy if state.get("evidence_report") else "tool_first",
            )
            for hit in state.get("retrieval_hits", [])
        ]
        trip_plan = trip_plan.model_copy(
            update={
                "citations": citations,
                "planning_trace_id": state["trace_id"],
                "evidence_report": state.get("evidence_report"),
            }
        )
        self._record(
            state["trace_id"],
            "planner",
            "candidate_plan_generated",
            {
                "days": len(trip_plan.days),
                "candidate_attractions": sum(len(day.attractions) for day in trip_plan.days),
                "citation_count": len(citations),
                "evidence_strategy": state["evidence_report"].strategy if state.get("evidence_report") else "unknown",
                "context_sufficient": state["evidence_report"].sufficient if state.get("evidence_report") else False,
            },
        )

        print(f"{'='*60}")
        print(f"✅ 旅行计划生成完成!")
        print(f"{'='*60}\n")

        return {"trip_plan": trip_plan}

    def _optimize_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """使用 CP-SAT 对候选景点执行选择、排序与时间窗排程。"""
        optimized = optimize_itinerary(state["trip_plan"], state["request"])
        report = optimized.optimization_report
        self._record(
            state["trace_id"],
            "optimize",
            "cp_sat_completed",
            report.model_dump(mode="json") if report else {"status": "missing"},
        )
        return {"trip_plan": optimized}

    def _validate_node(self, state: TripPlannerState) -> Dict[str, Any]:
        report = validate_trip_plan(
            state["trip_plan"],
            state["request"],
            repair_attempted=state["repair_attempts"] > 0,
        )
        plan = state["trip_plan"].model_copy(update={"validation_report": report})
        self._record(
            state["trace_id"],
            "validate",
            "constraint_validation_completed",
            {
                "passed": report.passed,
                "score": report.score,
                "issue_codes": [issue.code for issue in report.issues],
                "repair_attempted": report.repair_attempted,
            },
        )
        return {"validation_report": report, "trip_plan": plan}

    @staticmethod
    def _next_after_validation(state: TripPlannerState) -> str:
        report = state.get("validation_report")
        if report and not report.passed and state.get("repair_attempts", 0) < 1:
            return "repair"
        return "end"

    def _repair_node(self, state: TripPlannerState) -> Dict[str, Any]:
        """把确定性校验问题反馈给 Planner，最多进行一次受控重规划。"""
        report = state["validation_report"]
        issue_text = "\n".join(
            f"- {issue.code} ({issue.path}): {issue.message}; expected={issue.expected}; actual={issue.actual}"
            for issue in report.issues
            if issue.severity == "error"
        )
        query = f"""下面的旅行计划没有通过确定性约束校验。请只修复列出的问题，保留已有真实信息，
不要猜测坐标或添加无证据的事实，并返回与原计划完全相同 Schema 的 JSON。

校验问题：
{issue_text}

原计划：
{state['trip_plan'].model_dump_json(exclude={'validation_report'}, indent=2)}
"""
        result = self.planner_agent.invoke({"messages": [HumanMessage(content=query)]})
        self._record(
            state["trace_id"],
            "repair",
            "repair_requested",
            {"hard_issue_codes": [issue.code for issue in report.issues if issue.severity == "error"]},
        )
        repaired = self._parse_response(result["messages"][-1].content, state["request"])
        repaired = repaired.model_copy(
            update={
                "citations": state["trip_plan"].citations,
                "planning_trace_id": state["trace_id"],
            }
        )
        return {"trip_plan": repaired, "repair_attempts": state["repair_attempts"] + 1}

    def _build_planner_query(
        self,
        request: TripRequest,
        attractions: str,
        weather: str,
        hotels: str,
        retrieved_context: str,
    ) -> str:
        """构建行程规划查询 - 将三个子Agent的结果整合为prompt"""
        query = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

**基本信息:**
- 城市: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.travel_days}天
- 交通方式: {request.transportation}
- 住宿: {request.accommodation}
- 偏好: {', '.join(request.preferences) if request.preferences else '无'}

**景点信息:**
{attractions}

**天气信息:**
{weather}

**酒店信息:**
{hotels}

**用户上传资料的检索证据:**
{retrieved_context}

**要求:**
1. 每天最多安排{request.max_daily_attractions}个景点
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从酒店信息中选择)
4. 考虑景点之间的距离和交通方式
5. 返回完整的JSON格式数据
6. 景点的经纬度坐标要真实准确
7. 总预算上限: {request.max_budget if request.max_budget is not None else '未设置'}
8. 特殊约束: {', '.join(request.accessibility_needs) if request.accessibility_needs else '无'}
9. 优先使用检索证据中的用户订单、票据和明确偏好，不得虚构证据中没有的事实
10. 每个景点提供开放/关闭时间、0-100优先级及0-1证据置信度，无法确认时使用保守默认值
"""
        if request.free_text_input:
            query += f"\n**额外要求:** {request.free_text_input}"

        return query

    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """解析Agent响应为TripPlan对象

        支持从markdown代码块或纯JSON中提取数据。
        """
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("响应中未找到JSON数据")

            data = json.loads(json_str)
            return TripPlan(**data)

        except Exception as e:
            raise ValueError(f"Planner 返回内容无法解析为 TripPlan: {e}") from e

    def plan_trip(self, request: TripRequest) -> TripPlan:
        """
        使用多智能体协作生成旅行计划

        Args:
            request: 旅行请求

        Returns:
            旅行计划
        """
        trace_id = uuid.uuid4().hex
        started = time.perf_counter()
        try:
            initial_state: TripPlannerState = {
                "request": request,
                "attractions_data": "",
                "weather_data": "",
                "hotels_data": "",
                "retrieved_context": "",
                "retrieval_hits": [],
                "evidence_report": None,
                "trip_plan": None,
                "validation_report": None,
                "repair_attempts": 0,
                "trace_id": trace_id,
                "error": None,
            }

            final_state = self.graph.invoke(initial_state)
            if not final_state.get("trip_plan"):
                raise RuntimeError("工作流结束但没有生成旅行计划")
            plan = final_state["trip_plan"]
            get_experience_store().save_episode(
                trace_id,
                request,
                plan,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            self._record(trace_id, "end", "plan_completed", {"success": True})
            return plan

        except Exception as e:
            print(f"❌ 生成旅行计划失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self._record(trace_id, "error", "plan_failed", {"error_type": type(e).__name__, "message": str(e)[:500]})
            raise RuntimeError(f"旅行规划工作流执行失败: {e}") from e

    def replan_trip(self, request: TripRequest, current_plan: TripPlan, disruption: Disruption) -> TripPlan:
        """针对扰动重规划受影响日期，并强制保留其他日期，降低不必要变更。"""
        started = time.perf_counter()
        trace_id = uuid.uuid4().hex
        effective_request = request
        if disruption.type == "budget_changed" and disruption.new_budget is not None:
            effective_request = request.model_copy(update={"max_budget": disruption.new_budget})

        affected_dates = {disruption.date} if disruption.date else {day.date for day in current_plan.days}
        self._record(
            trace_id,
            "replan",
            "disruption_received",
            {
                "parent_trace_id": current_plan.planning_trace_id,
                "type": disruption.type,
                "date": disruption.date,
                "target": disruption.target,
                "affected_dates": sorted(affected_dates),
            },
        )
        prompt = f"""旅行过程中出现了新的扰动，请生成更新后的完整TripPlan JSON。
只修改日期 {sorted(affected_dates)} 对应的行程，其他日期必须保持不变；优先进行最小修改。
如果景点关闭，删除该景点并选择时空距离和用户偏好最接近的替代项。不得虚构无法验证的坐标。

扰动：
{disruption.model_dump_json(indent=2)}

当前计划：
{current_plan.model_dump_json(exclude={'validation_report', 'optimization_report', 'citations'}, indent=2)}
"""
        result = self.planner_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        candidate = self._parse_response(result["messages"][-1].content, effective_request)

        candidate_by_date = {day.date: day for day in candidate.days}
        merged_days = []
        for original_day in current_plan.days:
            if original_day.date in affected_dates and original_day.date in candidate_by_date:
                changed_day = candidate_by_date[original_day.date]
                if disruption.type == "attraction_closed" and disruption.target:
                    changed_day = changed_day.model_copy(
                        update={
                            "attractions": [
                                attraction
                                for attraction in changed_day.attractions
                                if attraction.name != disruption.target
                            ]
                        }
                    )
                merged_days.append(changed_day)
            else:
                merged_days.append(original_day)

        candidate = candidate.model_copy(
            update={
                "days": merged_days,
                "citations": current_plan.citations,
                "evidence_report": current_plan.evidence_report,
                "planning_trace_id": trace_id,
                "revision": current_plan.revision + 1,
            }
        )
        optimized = optimize_itinerary(candidate, effective_request)
        optimized_by_date = {day.date: day for day in optimized.days}
        stable_days = [
            optimized_by_date.get(day.date, day) if day.date in affected_dates else day
            for day in current_plan.days
        ]
        optimized = optimized.model_copy(update={"days": stable_days})
        report = validate_trip_plan(optimized, effective_request, repair_attempted=True)
        final_plan = optimized.model_copy(update={"validation_report": report})
        self._record(
            trace_id,
            "replan",
            "local_replan_completed",
            {
                "revision": final_plan.revision,
                "affected_dates": sorted(affected_dates),
                "validation_score": report.score,
            },
        )
        get_experience_store().save_episode(
            trace_id,
            effective_request,
            final_plan,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return final_plan

    @staticmethod
    def _record(trace_id: str, stage: str, event_type: str, payload: Dict[str, Any]) -> None:
        """可观测性失败不能中断主业务。"""
        try:
            get_experience_store().record_event(trace_id, stage, event_type, payload)
        except Exception as exc:
            print(f"⚠️ 记录飞轮事件失败: {exc}")

    # ============ 兼容旧版health_check接口 ============

    @property
    def agent(self):
        """兼容属性 - 用于trip.py中的health_check访问agent.name等"""
        return self

    @property
    def name(self) -> str:
        """兼容属性 - Agent名称"""
        return "LangGraph多智能体旅行规划系统"

    def list_tools(self) -> List[Any]:
        """兼容方法 - 返回可用工具列表"""
        try:
            return get_mcp_tools()
        except Exception:
            return []


# ============ 全局单例 ============

_multi_agent_planner = None


def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取多智能体旅行规划系统实例(单例模式)"""
    global _multi_agent_planner

    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()

    return _multi_agent_planner
