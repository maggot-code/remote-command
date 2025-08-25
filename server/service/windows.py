from server.service.dispatcher import register_executor

@register_executor("windows", default_port=5985, support_nopwd=True)
def execute_command(dto: dict) -> dict:
    # Windows 执行逻辑暂时 pass
    return {"msg": "Windows executed", "data": dto}
