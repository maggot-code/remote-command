
"""
动态inventory生成。
"""
from remote_call.utils import write_temp_file
from remote_call.context import RemoteCallContext
from ansible.config import AnsibleConfig
import logging

logger = logging.getLogger('ansible')

def generate_inventory(
	user_ctx: 'RemoteCallContext',
	ansible_cfg: 'AnsibleConfig',
	extra_vars: dict = None
) -> tuple[str, callable]:
	"""
	动态生成ansible inventory内容并写入临时文件
	:param user_ctx: RemoteCallContext 用户参数上下文
	:param ansible_cfg: AnsibleConfig ansible配置上下文
	:param extra_vars: 额外参数
	:return: (文件路径, 清理函数)
	"""
	group_name = user_ctx.get_group_name()
	host_params = [
		f"{user_ctx.ip}",
		f"ansible_user={user_ctx.username}",
		f"ansible_port={user_ctx.port}"
	]
	# 认证参数
	host_params.extend(user_ctx.get_auth_params(ansible_cfg))
	# SSH参数
	ssh_args = user_ctx.get_ssh_args(ansible_cfg)
	if ssh_args:
		host_params.append(f"ansible_ssh_common_args='{ssh_args}'")
	# 额外参数
	if extra_vars:
		for k, v in extra_vars.items():
			host_params.append(f"{k}={v}")

	host_line = ' '.join(host_params)
	content = f"[{group_name}]\n{host_line}\n"

	logger.info("[Inventory Content]:\n%s", content)

	file_path, close_func, cleanup_func = write_temp_file(content, suffix=".ini")
	close_func()
	return file_path, cleanup_func
