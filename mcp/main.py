from remote_call_mcp.server_http import mcp


def main():
    # 启动基于 Streamable HTTP 的 MCP 服务，默认监听本地 3333 端口
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8848, path="/mcp")
    except KeyboardInterrupt:
        # 友好退出：抑制堆栈打印，返回 0 状态码
        pass


if __name__ == "__main__":
    main()
