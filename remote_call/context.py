"""
参数上下文对象 RemoteCallContext

用于存储和处理远程调用相关参数，仅接收已校验参数，聚焦于业务逻辑和方法封装。
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class RemoteCallContext:
    os_type: str
    ip: str
    username: str
    password: Optional[str] = None
    port: int = 22
    command: Optional[str] = None
    file_path: Optional[str] = None
    use_bastion: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    def is_linux(self) -> bool:
        """
        判断当前上下文目标主机是否为 Linux 系统。
        :return: 是 Linux 返回 True，否则返回 False。
        """
        return self.os_type.lower() == "linux"

    def is_windows(self) -> bool:
        """
        判断当前上下文目标主机是否为 Windows 系统。
        :return: 是 Windows 返回 True，否则返回 False。
        """
        return self.os_type.lower() == "windows"

    def is_command_mode(self) -> bool:
        """
        判断是否为命令执行模式（即只执行单条命令）。
        :return: 命令模式返回 True，否则返回 False。
        """
        return self.command is not None and self.file_path is None

    def is_script_mode(self) -> bool:
        """
        判断是否为脚本执行模式（即上传并执行脚本文件）。
        :return: 脚本模式返回 True，否则返回 False。
        """
        return self.file_path is not None and self.command is None
    
    def is_password_auth(self) -> bool:
        """
        判断当前认证方式是否为密码认证。
        :return: 使用密码认证返回 True，否则返回 False。
        """
        return self.password is not None

    def is_use_bastion(self) -> bool:
        """
        判断当前连接是否需要经过堡垒机（跳板机）。
        :return: 需要堡垒机返回 True，否则返回 False。
        """
        return self.use_bastion

    def get_target_addr(self) -> str:
        """
        获取目标主机的地址（IP:端口）。
        :return: 形如 '192.168.1.1:22' 的字符串。
        """
        return f"{self.ip}:{self.port}"
    
    def get_group_name(self) -> str:
        """
        根据操作系统类型返回合适的 ansible group_name。
        :return: Linux 返回 'linux_servers'，Windows 返回 'windows_servers'，否则返回 'target'。
        """
        if self.is_linux():
            return "linux_servers"
        elif self.is_windows():
            return "windows_servers"
        return "target"
    
    def get_auth_params(self, ansible_cfg=None) -> list:
        """
        获取 ansible inventory 主机认证相关参数（密码/密钥）。
        :param ansible_cfg: 可选，AnsibleConfig对象，提供密钥路径等信息。
        :return: 认证参数列表，如 ['ansible_password=xxx'] 或 ['ansible_ssh_private_key_file=xxx']。
        """
        params = []
        if self.is_password_auth():
            # 密码认证时只返回密码参数，不添加密钥参数
            params.append(f"ansible_password={self.password}")
            return params
        # 仅密钥认证且 use_bastion 为 True 时添加密钥参数
        if ansible_cfg and self.is_use_bastion():
            key_path = getattr(ansible_cfg, 'bastion_temp_private_key', None) or self.extra.get('private_key', '')
            if key_path:
                params.append(f"ansible_ssh_private_key_file={key_path}")
        return params

    def get_ssh_args(self, ansible_cfg=None) -> str:
        """
        获取 ansible_ssh_common_args 参数（含跳板/直连）。
        :param ansible_cfg: 可选，AnsibleConfig对象，提供跳板机相关信息。
        :return: SSH 连接参数字符串。
        """
        # 密码认证时不添加 ssh_common_args
        if self.is_password_auth():
            return ""
        if not self.is_use_bastion() or not ansible_cfg:
            # 直连模式，仅关闭主机密钥检查
            return "-o StrictHostKeyChecking=no"
        # 跳板模式，拼接 ProxyJump 及密钥参数
        return (
            f"-o ProxyJump={ansible_cfg.bastion_user}@{ansible_cfg.bastion_ip} "
            f"-o StrictHostKeyChecking=no -i {ansible_cfg.jump_private_key}"
        )

    def to_dict(self) -> dict:
        """
        将当前上下文对象转为字典。
        :return: 包含所有参数的字典。
        """
        d = self.__dict__.copy()
        # 保证 use_bastion 字段一定存在
        if 'use_bastion' not in d:
            d['use_bastion'] = True
        return d

