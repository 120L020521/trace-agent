"""旅行资料抽取：文本/PDF 直接解析，图片交给视觉语言模型结构化理解。"""

from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Tuple

from langchain_core.messages import HumanMessage

from .llm_service import get_llm


TEXT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
}
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def extract_document(filename: str, content_type: str, payload: bytes) -> Tuple[str, dict]:
    """返回适合进入知识库的文本和抽取元数据。"""
    suffix = Path(filename).suffix.lower()
    if content_type in TEXT_TYPES or suffix in {".txt", ".md", ".json", ".csv"}:
        return payload.decode("utf-8", errors="replace"), {"extractor": "plain-text"}
    if content_type == "application/pdf" or suffix == ".pdf":
        return _extract_pdf(payload), {"extractor": "pypdf"}
    if content_type in IMAGE_TYPES or suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return _extract_image_with_vlm(content_type or "image/jpeg", payload), {"extractor": "vision-language-model"}
    raise ValueError(f"暂不支持的文件类型: {content_type or suffix}")


def _extract_pdf(payload: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(payload))
    pages = []
    for index, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"[第{index + 1}页]\n{text}")
    if not pages:
        raise ValueError("PDF 未提取到文本；扫描版 PDF 请先转为图片上传")
    return "\n\n".join(pages)


def _extract_image_with_vlm(content_type: str, payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    prompt = """请读取这张旅行相关截图、订单、车票或攻略图片。只提取图片中有明确证据的信息，
包括地点、日期时间、价格、订单/车次、营业时间、限制条件和注意事项。不要补充图片中不存在的事实。
以简洁 Markdown 输出，并保留关键原文，方便后续检索和引用。"""
    response = get_llm().invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{encoded}"}},
                ]
            )
        ]
    )
    content = response.content
    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "") if isinstance(item, dict) else str(item) for item in content
        )
    if not str(content).strip():
        raise ValueError("视觉模型没有返回可索引内容")
    return str(content).strip()
