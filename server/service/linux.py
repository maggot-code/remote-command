from server.service.dispatcher import register_executor
from server.biz.linux import biz_execute_command,biz_execute_command_nopwd,biz_script

@register_executor("linux", default_port=22, support_nopwd=True)
def execute_command(dto: dict) -> dict:
    return biz_execute_command(dto)

@register_executor("linux_nopwd", default_port=22, support_nopwd=True)
def execute_command_nopwd(dto: dict) -> dict:
    return biz_execute_command_nopwd(dto)

@register_executor("linux_script", default_port=22, support_nopwd=True)
def execute_script(dto: dict) -> dict:
    return biz_script(dto)
