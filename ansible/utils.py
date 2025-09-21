import paramiko
import os

def fetch_bastion_key(user_context, config_context):
	"""
	从堡垒机拉取密钥到本地临时路径，参数全部从上下文获取
	:param user_context: RemoteCallContext
	:param config_context: AnsibleConfig
	:return: 本地密钥路径
	"""
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# 用 JUMP_PRIVATE_KEY 连接堡垒机
	ssh.connect(
		config_context.bastion_ip,
		username=config_context.bastion_user,
		key_filename=config_context.jump_private_key
	)
	sftp = ssh.open_sftp()
	# 从堡垒机拉取 BASTION_PRIVATE_KEY 到本地 BASTION_TEMP_PRIVATE_KEY
	sftp.get(config_context.bastion_private_key, config_context.bastion_temp_private_key)
	sftp.close()
	ssh.close()
	os.chmod(config_context.bastion_temp_private_key, 0o600)

	def cleanup():
		try:
			if os.path.exists(config_context.bastion_temp_private_key):
				os.remove(config_context.bastion_temp_private_key)
		except Exception:
			pass
	return cleanup

def extract_ansible_events(r):
	"""
	提取 ansible_runner 事件，按主机聚合输出和错误。
	"""
	results = []
	error = None
	focus_event_data = None
	for event in getattr(r, 'events', []):
		if event.get("event") == "runner_on_ok":
			host = event["event_data"].get("host")
			res = event["event_data"].get("res", {})
			result_item = {
				"host": host,
				"stdout": res.get("stdout", ""),
				"stderr": res.get("stderr", ""),
				"rc": res.get("rc", 0),
				"msg": res.get("msg", ""),
				"changed": res.get("changed", False),
			}
			results.append(result_item)
			# 只保留第一个runner_on_ok的event_data作为target（主任务）
			if not focus_event_data:
				focus_event_data = event["event_data"]
		elif event.get("event") in ("runner_on_failed", "runner_on_unreachable"):
			host = event["event_data"].get("host")
			res = event["event_data"].get("res", {})
			result_item = {
				"host": host,
				"stdout": res.get("stdout", ""),
				"stderr": res.get("stderr", ""),
				"rc": res.get("rc", 1),
				"msg": res.get("msg", ""),
				"failed": True,
			}
			results.append(result_item)
			error = res
		else:
			continue
	return results, error, focus_event_data