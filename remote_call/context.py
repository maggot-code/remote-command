"""
参数上下文对象，负责存储和处理远程调用相关参数。
只接收已校验参数，聚焦业务逻辑和方法。
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
        """判断是否为Linux节点"""
        return self.os_type.lower() == "linux"

    def is_windows(self) -> bool:
        """判断是否为Windows节点"""
        return self.os_type.lower() == "windows"

    def is_command_mode(self) -> bool:
        """判断是否为命令执行模式"""
        return self.command is not None and self.file_path is None

    def is_script_mode(self) -> bool:
        """判断是否为脚本执行模式"""
        return self.file_path is not None and self.command is None
    
    def is_password_auth(self) -> bool:
        """判断是否为密码认证"""
        return self.password is not None

    def is_use_bastion(self) -> bool:
        """判断是否使用堡垒机"""
        return self.use_bastion

    def get_target_addr(self) -> str:
        """返回目标主机地址（可扩展端口等）"""
        return f"{self.ip}:{self.port}"
    
    def get_group_name(self) -> str:
        """
        根据操作系统类型返回合适的ansible group_name
        """
        if self.is_linux():
            return "linux_servers"
        elif self.is_windows():
            return "windows_servers"
        return "target"
    
    def get_auth_params(self, ansible_cfg=None) -> list:
        """
        返回ansible inventory主机认证相关参数（密码/密钥）
        :param ansible_cfg: 可选，AnsibleConfig对象
        :return: [str, ...]
        """
        params = []
        if self.is_password_auth():
            params.append(f"ansible_password={self.password}")
            # 密码认证时不添加密钥参数
            return params
        # 仅密钥认证且 use_bastion 为 True 时添加密钥参数
        if ansible_cfg and self.is_use_bastion():
            key_path = getattr(ansible_cfg, 'bastion_temp_private_key', None) or self.extra.get('private_key', '')
            if key_path:
                params.append(f"ansible_ssh_private_key_file={key_path}")
        return params

    def get_ssh_args(self, ansible_cfg=None) -> str:
        """
        返回ansible_ssh_common_args参数（含跳板/直连）
        :param ansible_cfg: 可选，AnsibleConfig对象
        :return: str
        """
        # 密码认证时不添加ssh_common_args
        if self.is_password_auth():
            return ""
        if not self.is_use_bastion() or not ansible_cfg:
            # 直连模式
            return "-o StrictHostKeyChecking=no"
        # 跳板模式
        return (
            f"-o ProxyJump={ansible_cfg.bastion_user}@{ansible_cfg.bastion_ip} "
            f"-o StrictHostKeyChecking=no -i {ansible_cfg.jump_private_key}"
        )

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        if 'use_bastion' not in d:
            d['use_bastion'] = True
        return d

