from pydantic import BaseModel, Field

class BaseHostDTO(BaseModel):
    ip: str = Field(..., description="目标主机IP")
    username: str = Field(..., description="用户名")
    os_type: str = Field("linux", description="操作系统类型:linux/windows")

class CommandDTO(BaseHostDTO):
    password: str = Field(..., description="密码，必须提供")
    port: int = Field(..., description="端口,Linux默认22,Windows默认5985")
    command: str = Field(..., description="要执行的命令")

class NoPwdCommandDTO(BaseModel):
    ip: str = Field(..., description="目标主机IP")
    username: str = Field(..., description="用户名")
    os_type: str = Field("linux", description="操作系统类型:linux/windows")
    port: int = Field(..., description="端口,Linux默认22,Windows默认5985")
    command: str = Field(..., description="要执行的命令")

class ScriptDTO(BaseHostDTO):
    ip: str = Field(..., description="目标主机IP")
    username: str = Field(..., description="用户名")
    os_type: str = Field("linux", description="操作系统类型:linux/windows")
    port: int = Field(..., description="端口,Linux默认22,Windows默认5985")
    file_path: str = Field(..., description="本地脚本路径")
    remote_host: str = Field(..., description="远程目标路径")