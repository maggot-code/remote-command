
"""
堡垒机及ansible相关内部配置。
"""

import os
from django.conf import settings

class AnsibleConfig:
	"""
	ansible相关配置上下文，支持从settings.BASTION_CONFIG或环境变量读取
	"""
	def __init__(self):
		cfg = getattr(settings, "BASTION_CONFIG", {})
		self.working_dir = os.path.expanduser(cfg.get("WORKING_DIR") or os.getenv("WORKING_DIR") or "")
		self.bastion_ip = cfg.get("BASTION_IP") or os.getenv("BASTION_IP")
		self.bastion_user = cfg.get("BASTION_USER") or os.getenv("BASTION_USER")
		self.bastion_private_key = os.path.expanduser(cfg.get("BASTION_PRIVATE_KEY") or os.getenv("BASTION_PRIVATE_KEY") or "")
		self.bastion_temp_private_key = os.path.expanduser(cfg.get("BASTION_TEMP_PRIVATE_KEY") or os.getenv("BASTION_TEMP_PRIVATE_KEY") or "")
		self.jump_private_key = os.path.expanduser(cfg.get("JUMP_PRIVATE_KEY") or os.getenv("JUMP_PRIVATE_KEY") or "")

	def to_dict(self):
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
	获取ansible内部配置上下文对象
	:return: AnsibleConfig实例
	"""
	return AnsibleConfig()

