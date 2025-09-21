"""
堡垒机及 ansible 相关内部配置。
包含 ansible 配置上下文的定义与获取。
"""

import os
from django.conf import settings


class AnsibleConfig:
	"""
	ansible 相关配置上下文。
	支持从 settings.BASTION_CONFIG 或环境变量读取配置。
	"""

	def __init__(self):
		"""
		初始化 ansible 配置。
		优先从 Django settings 的 BASTION_CONFIG 读取配置，若无则回退到环境变量。
		关键路径均自动展开用户目录。
		"""
		cfg = getattr(settings, "BASTION_CONFIG", {})  # 获取 Django settings 中的堡垒机配置字典
		# 工作目录，优先级：settings > 环境变量 > 空字符串
		self.working_dir = os.path.expanduser(
			cfg.get("WORKING_DIR") or os.getenv("WORKING_DIR") or ""
		)
		
		# 堡垒机 IP 地址
		self.bastion_ip = cfg.get("BASTION_IP") or os.getenv("BASTION_IP")
		
		# 堡垒机登录用户名
		self.bastion_user = cfg.get("BASTION_USER") or os.getenv("BASTION_USER")
		
		# 堡垒机私钥路径
		self.bastion_private_key = os.path.expanduser(
			cfg.get("BASTION_PRIVATE_KEY") or os.getenv("BASTION_PRIVATE_KEY") or ""
		)
		
		# 堡垒机临时私钥路径（如有临时密钥需求）
		self.bastion_temp_private_key = os.path.expanduser(
			cfg.get("BASTION_TEMP_PRIVATE_KEY") or os.getenv("BASTION_TEMP_PRIVATE_KEY") or ""
		)
		
		# 跳板机私钥路径（如有多级跳板需求）
		self.jump_private_key = os.path.expanduser(
			cfg.get("JUMP_PRIVATE_KEY") or os.getenv("JUMP_PRIVATE_KEY") or ""
		)

	def to_dict(self):
		"""
		将配置对象转为字典，便于序列化或调试。
		:return: dict 形式的 ansible 配置
		"""
		return {
			"WORKING_DIR": self.working_dir,
			"BASTION_IP": self.bastion_ip,
			"BASTION_USER": self.bastion_user,
			"BASTION_PRIVATE_KEY": self.bastion_private_key,
			"BASTION_TEMP_PRIVATE_KEY": self.bastion_temp_private_key,
			"JUMP_PRIVATE_KEY": self.jump_private_key,
		}


def get_ansible_config() -> AnsibleConfig:
	"""
	获取 ansible 内部配置上下文对象。
	:return: AnsibleConfig 实例
	"""
	return AnsibleConfig()

