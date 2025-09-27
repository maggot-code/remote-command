"""
动态生成 Ansible inventory 文件。
本模块根据用户上下文和 Ansible 配置，动态拼接 inventory 内容并写入临时文件，
用于后续 ansible-playbook 或 ansible 命令的调用。
"""
from typing import Tuple, Callable
from remote_call.utils import write_temp_file
from remote_call.context import RemoteCallContext
from ansible.config import AnsibleConfig
import logging

logger = logging.getLogger('django')

def generate_inventory(
	user_ctx: 'RemoteCallContext',
	ansible_cfg: 'AnsibleConfig',
	extra_vars: dict = None
) -> Tuple[str, Callable]:
	"""
	动态生成 ansible inventory 内容并写入临时文件。

	Args:
		user_ctx (RemoteCallContext): 用户参数上下文，包含主机、端口、认证等信息。
		ansible_cfg (AnsibleConfig): ansible 配置上下文。
		extra_vars (dict, optional): 额外的主机变量参数，会追加到 inventory 主机行。

	Returns:
		tuple[str, callable]: (inventory 文件路径, 清理函数)
	"""
	# 获取主机分组名
	group_name = user_ctx.get_group_name()

	# 构建主机参数列表，基础参数：IP、用户名、端口
	host_params = [
		f"{user_ctx.ip}",
		f"ansible_user={user_ctx.username}",
		f"ansible_port={user_ctx.get_port()}"  # 修改为调用 get_port() 方法
	]
	
    # 添加基础参数
	if user_ctx.is_linux():
		host_params.append(user_ctx.get_linux_inventory())
	if user_ctx.is_windows():
		host_params.append(user_ctx.get_windows_inventory())
	if user_ctx.is_h3c():
		host_params.append(user_ctx.get_h3c_inventory())

	# 添加认证参数（如密码/密钥等）
	host_params.extend(user_ctx.get_auth_params(ansible_cfg))

	# 拼接 SSH 相关参数（如跳板机、代理等）
	ssh_args = user_ctx.get_ssh_args(ansible_cfg)
	if ssh_args:
		# ansible_ssh_common_args 需用单引号包裹
		host_params.append(f"ansible_ssh_common_args='{ssh_args}'")

	# 追加额外参数（如自定义变量）
	if extra_vars:
		for k, v in extra_vars.items():
			host_params.append(f"{k}={v}")

	# 拼接主机行内容
	host_line = ' '.join(host_params)
	# 组装 inventory 文件内容
	content = f"[{group_name}]\n{host_line}\n"

	# 日志记录 inventory 内容，便于调试
	logger.info("[Inventory Content : ERP - %s]:\n%s",user_ctx.get_erp(), content)

	# 写入临时文件，返回文件路径和清理函数
	file_path, close_func, cleanup_func = write_temp_file(content, suffix=".ini")
	close_func()  # 立即关闭文件句柄，防止资源泄漏
	return file_path, cleanup_func