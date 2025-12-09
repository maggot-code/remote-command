from typing import Annotated

import httpx
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from pydantic import Field

# Streamable HTTP MCP server with a single tool that calls an upstream HTTP API.
# Endpoint provided by user: 172.31.32.56:8000/api/v1/remote_call/
REMOTE_URL = "http://172.31.32.56:8000/api/v1/remote_call/"

mcp = FastMCP(
    name="undev-remote-call",
    strict_input_validation=True,
)


@mcp.tool(
    name="remote_call",
    description=(
        "调用远程执行接口，传入 IP、TYPE、CMD 三个参数并返回上游结果。"
    ),
    tags={"http", "remote", "command"},
)
async def remote_call(
    ip: Annotated[str, Field(min_length=1, max_length=128, description="目标主机 IP 地址")],
    type: Annotated[str, Field(min_length=1, max_length=64, description="命令类型 TYPE（由上游定义）")],
    cmd: Annotated[str, Field(min_length=1, max_length=4096, description="要执行的命令字符串 CMD")],
    timeout_secs: Annotated[float, Field(ge=1, le=120, description="上游请求超时（秒）")] = 30.0,
    ctx: Context | None = None,
) -> dict:
    """向上游接口发起调用并返回 JSON 结果。

    - 使用 Streamable HTTP 传输；执行过程通过 ctx.* 产生流式日志/进度。
    - 入参严格校验，超时可配置；错误通过 ToolError 语义化返回。
    """

    if ctx is not None:
        await ctx.info("准备调用远程执行接口…")
        await ctx.report_progress(1, total=3)

    payload = {"IP": ip, "TYPE": type, "CMD": cmd}

    try:
        if ctx is not None:
            await ctx.debug(f"POST {REMOTE_URL}")

        async with httpx.AsyncClient(timeout=timeout_secs, follow_redirects=False) as client:
            resp = await client.post(REMOTE_URL, json=payload)

        if ctx is not None:
            await ctx.report_progress(2, total=3)

        # Raise for non-2xx
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Capture upstream error body if any
            detail = None
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            if ctx is not None:
                await ctx.error(f"上游返回非 2xx 状态码: {e.response.status_code}")
            raise ToolError(
                f"上游 API 错误: {e.response.status_code}",
                extra={"upstream": detail},
            ) from None

        # Parse JSON body
        try:
            data = resp.json()
        except ValueError:
            if ctx is not None:
                await ctx.error("上游返回非 JSON 响应。")
            raise ToolError("上游返回非 JSON 响应。") from None

        if ctx is not None:
            await ctx.report_progress(3, total=3)
            await ctx.info("远程调用完成。")

        # 返回原样数据，避免敏感字段泄露风险由上游控制
        return {
            "ok": True,
            "status": resp.status_code,
            "data": data,
        }

    except httpx.RequestError as e:
        if ctx is not None:
            await ctx.error(f"网络异常：{str(e)}")
        raise ToolError("网络请求失败，无法连接上游接口。") from None


# Also expose an ASGI app for uvicorn-based deployments if desired.
app = mcp.http_app(path="/mcp")
