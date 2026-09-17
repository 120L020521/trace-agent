"""高德地图服务封装 - 基于新版MCP服务层"""

from typing import List, Dict, Any, Optional
from ..models.schemas import Location, POIInfo, WeatherInfo
from .mcp_service import get_mcp_service


class AmapService:
    """高德地图服务封装类 - 通过MCP服务调用amap-mcp-server"""

    def __init__(self):
        """初始化服务"""
        self.mcp_service = get_mcp_service()

    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """
        搜索POI

        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内

        Returns:
            POI信息列表
        """
        try:
            tool = self.mcp_service.get_tool_by_name("maps_text_search")
            if not tool:
                print("❌ 未找到maps_text_search工具")
                return []

            result = tool.invoke({
                "keywords": keywords,
                "city": city,
                "citylimit": str(citylimit).lower()
            })

            print(f"POI搜索结果: {str(result)[:200]}...")
            # TODO: 解析实际的POI数据并返回POIInfo列表
            return []

        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []

    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气

        Args:
            city: 城市名称

        Returns:
            天气信息列表
        """
        try:
            tool = self.mcp_service.get_tool_by_name("maps_weather")
            if not tool:
                print("❌ 未找到maps_weather工具")
                return []

            result = tool.invoke({"city": city})
            print(f"天气查询结果: {str(result)[:200]}...")
            # TODO: 解析实际的天气数据并返回WeatherInfo列表
            return []

        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []

    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        规划路线

        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)

        Returns:
            路线信息
        """
        try:
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }

            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")
            tool = self.mcp_service.get_tool_by_name(tool_name)
            if not tool:
                print(f"❌ 未找到{tool_name}工具")
                return {}

            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address
            }

            if origin_city:
                arguments["origin_city"] = origin_city
            if destination_city:
                arguments["destination_city"] = destination_city

            result = tool.invoke(arguments)
            print(f"路线规划结果: {str(result)[:200]}...")
            return {"raw": result}

        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码(地址转坐标)

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        try:
            tool = self.mcp_service.get_tool_by_name("maps_geo")
            if not tool:
                print("❌ 未找到maps_geo工具")
                return None

            arguments = {"address": address}
            if city:
                arguments["city"] = city

            result = tool.invoke(arguments)
            print(f"地理编码结果: {str(result)[:200]}...")
            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        try:
            tool = self.mcp_service.get_tool_by_name("maps_search_detail")
            if not tool:
                print("❌ 未找到maps_search_detail工具")
                return {}

            result = tool.invoke({"id": poi_id})
            print(f"POI详情结果: {str(result)[:200]}...")

            import json
            import re

            json_match = re.search(r'\{.*\}', str(result), re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return {"raw": result}

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service

    if _amap_service is None:
        _amap_service = AmapService()

    return _amap_service
