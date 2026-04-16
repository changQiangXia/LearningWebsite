import base64
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib import error, request

from django.conf import settings


class QwenServiceError(RuntimeError):
    """Raised when the Qwen API cannot satisfy a request."""


def qwen_is_enabled() -> bool:
    return bool(settings.QWEN_API_KEY.strip())


def _extract_message_content(payload: dict[str, Any]) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise QwenServiceError("Qwen 返回结果结构异常。") from exc

    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "\n".join(part.strip() for part in text_parts if part.strip())
    raise QwenServiceError("Qwen 返回了无法解析的内容类型。")


def _post_chat_completion(payload: dict[str, Any]) -> dict[str, Any]:
    endpoint = settings.QWEN_BASE_URL.rstrip("/") + "/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {settings.QWEN_API_KEY}",
        "Content-Type": "application/json",
    }
    req = request.Request(endpoint, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=settings.QWEN_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
            message = payload.get("message") or payload.get("error", {}).get("message") or body
        except json.JSONDecodeError:
            message = body or str(exc)
        raise QwenServiceError(f"Qwen 接口调用失败：{message}") from exc
    except error.URLError as exc:
        raise QwenServiceError("Qwen 接口暂时不可达，请稍后再试。") from exc


def generate_ai_dialogue_reply(message: str) -> str:
    if not qwen_is_enabled():
        raise QwenServiceError("未配置 Qwen API Key。")

    payload = {
        "model": settings.QWEN_CHAT_MODEL,
        "temperature": 0.6,
        "messages": [
            {
                "role": "system",
                "content": (
                "你是“走进人工智能”教学网站中的助教。"
                    "面向初中生，用简洁、准确、鼓励思考的中文回答。"
                    "优先围绕人工智能概念、应用、伦理、未来趋势来解释。"
                    "如果问题超出课程主题，也要尽量拉回到课程学习场景。"
                    "不要使用 Markdown、表情符号或项目符号。"
                    "回答控制在 120 到 180 字。"
                ),
            },
            {"role": "user", "content": message.strip()},
        ],
    }
    result = _post_chat_completion(payload)
    answer = _extract_message_content(result)
    if not answer:
        raise QwenServiceError("Qwen 没有返回有效回复。")
    return answer


def analyze_image_with_qwen(image_name: str, image_bytes: bytes, content_type: str | None = None) -> str:
    if not qwen_is_enabled():
        raise QwenServiceError("未配置 Qwen API Key。")

    guessed_type = content_type or mimetypes.guess_type(image_name)[0] or "image/jpeg"
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    image_url = f"data:{guessed_type};base64,{image_base64}"

    payload = {
        "model": settings.QWEN_VL_MODEL,
        "temperature": 0.3,
        "messages": [
            {
                "role": "system",
                "content": (
                "你是教学网站中的图像识别助教。"
                    "请用中文输出适合中学生阅读的识别结果。"
                    "请严格输出三行纯文本，分别以“主体：”“细节：”“场景：”开头。"
                    "不要使用 Markdown、编号、项目符号或表情符号。"
                    "先判断图片主体，再概括关键细节，最后说明这张图可能对应的场景或用途。"
                    "如果识别不确定，请明确说明“不完全确定”。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请识别这张图片，并给出简洁清晰的结果。"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    }
    result = _post_chat_completion(payload)
    answer = _extract_message_content(result)
    if not answer:
        raise QwenServiceError("Qwen 没有返回有效识别结果。")
    return answer


def normalize_uploaded_image_name(image_name: str) -> str:
    suffix = Path(image_name or "upload.jpg").suffix or ".jpg"
    return f"upload{suffix.lower()}"
