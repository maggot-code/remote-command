import paramiko
import os


def fetch_bastion_key(user_context, config_context):
	"""
	从堡垒机（跳板机）拉取密钥到本地临时路径。
    
	参数：
		user_context: RemoteCallContext，上下文用户信息（未直接用到，预留扩展）
		config_context: AnsibleConfig，包含堡垒机连接和密钥路径等配置
	返回：
		cleanup: 清理本地临时密钥文件的回调函数
	主要流程：
		1. 使用 paramiko 通过跳板机私钥建立 SSH 连接
		2. 通过 SFTP 拉取堡垒机上的目标私钥到本地临时路径
		3. 修改本地密钥权限为 600
		4. 返回一个 cleanup 回调用于后续清理本地密钥
	"""
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动接受未知主机密钥
	# 用跳板机私钥连接堡垒机
	ssh.connect(
		config_context.bastion_ip,
		username=config_context.bastion_user,
		key_filename=config_context.jump_private_key
	)
	
	sftp = ssh.open_sftp()
	# 从堡垒机拉取目标私钥到本地临时路径
	sftp.get(config_context.bastion_private_key, config_context.bastion_temp_private_key)
	sftp.close()
	ssh.close()
	# 设置本地密钥权限为 600，防止权限过宽被 SSH 拒绝
	os.chmod(config_context.bastion_temp_private_key, 0o600)

	def cleanup():
		"""
		清理本地临时密钥文件，异常时忽略错误。
		"""
		try:
			if os.path.exists(config_context.bastion_temp_private_key):
				os.remove(config_context.bastion_temp_private_key)
		except Exception:
			pass
	return cleanup


def extract_ansible_events(r):
	"""
	提取 ansible_runner 事件，按主机聚合输出和错误信息。
    
	参数：
		r: ansible_runner 的结果对象，需包含 events 属性（事件列表）
	返回：
		results: 按主机聚合的输出结果列表，每项包含主机、stdout、stderr、rc、msg、changed/failed 等
		error: 首个失败/不可达事件的 res 字典（如有）
		focus_event_data: 第一个 runner_on_ok 事件的 event_data（主任务目标）
	说明：
		- 只聚合 runner_on_ok、runner_on_failed、runner_on_unreachable 三类事件
		- 其他事件类型会被忽略
		- focus_event_data 便于后续定位主任务目标
	"""
	results = []
	error = None
	focus_event_data = None
	for event in getattr(r, 'events', []):
		# 处理成功事件
		if event.get("event") == "runner_on_ok":
			host = event["event_data"].get("host")
			res = event["event_data"].get("res", {})
			result_item = {
				"host": host,  # 主机名
				"stdout": res.get("stdout", ""),  # 命令标准输出
				"stderr": res.get("stderr", ""),  # 命令标准错误
				"rc": res.get("rc", 0),  # 返回码
				"msg": res.get("msg", ""),  # 附加消息
				"changed": res.get("changed", False),  # 是否有变更
			}
			results.append(result_item)
			# 只保留第一个 runner_on_ok 的 event_data 作为主任务目标
			if not focus_event_data:
				focus_event_data = event["event_data"]
		# 处理失败或不可达事件
		elif event.get("event") in ("runner_on_failed", "runner_on_unreachable"):
			host = event["event_data"].get("host")
			res = event["event_data"].get("res", {})
			result_item = {
				"host": host,
				"stdout": res.get("stdout", ""),
				"stderr": res.get("stderr", ""),
				"rc": res.get("rc", 1),  # 失败默认 rc=1
				"msg": res.get("msg", ""),
				"failed": True,  # 标记为失败
			}
			results.append(result_item)
			error = res  # 只保留第一个失败的错误信息
		else:
			# 其他事件类型忽略
			continue
	return results, error, focus_event_data