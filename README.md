
# Ansible 跳板机免密自动化平台

## 项目简介

本项目通过Django后端整合Ansible，实现堡垒机（跳板机）场景下对内网节点的自动化命令执行。平台支持多层SSH免密跳转，统一API接口，详细日志审计，适用于企业级自动化运维和合规追踪。

## 目录结构

```
.
├── ansible/           # Ansible相关封装与配置
├── api/               # Django API接口
├── artifacts/         # 任务执行产物与缓存
├── deploy/            # 部署相关脚本
├── logs/              # 日志文件
├── remote_call/       # 远程调用与上下文服务
├── server/            # Django服务端
├── test/              # 测试用例
├── manage.py
├── pyproject.toml
├── uv.lock
├── db.sqlite3
├── all.ini
└── README.md
```

## 环境依赖

- Python 3.9.6
- Django 4.2.23
- Ansible 8.7.0
- Ansible-runner 2.4.1
- OpenSSH（各节点版本见下表）

| 角色         | IP                | 用户      | 密钥/密码位置                        | OpenSSH版本         |
| ------------ | ----------------- | --------- | ------------------------------------ | ------------------- |
| Django Server| 192.168.199.196   | root      | /root/.ssh/id_rsa_ansible            | 9.9p2, LibreSSL 3.3.6|
| 堡垒机       | 192.168.27.131    | root      | /root/.ssh/id_rsa, /root/.ssh/authorized_keys | 8.7p1, OpenSSL 3.2.2|
| 内网节点     | 192.168.27.132    | internal-node | /home/internal-node/.ssh/authorized_keys | 8.7p1, OpenSSL 3.2.2|

## 系统架构

- Django Server与内网节点无法直连，需经堡垒机跳转。
- Django Server使用专用密钥对堡垒机免密，堡垒机再免密连接内网节点。
- 用户通过API提交命令请求，后端组装Ansible上下文，调用ansible_runner执行，结果经堡垒机回传。

<!-- 如有架构图可放置于docs/目录 -->

## 快速开始

1. 克隆项目并安装依赖

     ```bash
     git clone https://github.com/maggot-code/remote-command.git
     cd remote-command
     pip install -r requirements.txt
     ```

2. 配置堡垒机信息

     - 编辑 `ansible/config.py` 或相关配置文件，填写堡垒机IP、用户、密钥路径等。

3. 启动Django服务

     ```bash
     python manage.py migrate
     python manage.py runserver 0.0.0.0:8000
     ```

4. 访问API接口（示例）

     ```http
     POST /api/remote_call/
     Content-Type: application/json

     {
         "host": "192.168.27.132",
         "user": "internal-node",
         "command": "uname -a",
         "os_type": "linux"
     }
     ```

## API设计

- 统一返回格式：

    ```json
    {
        "code": 0,
        "msg": "success",
        "data": {
            "stdout": "...",
            "stderr": "...",
            "exit_code": 0,
            "start_time": "...",
            "end_time": "..."
        }
    }
    ```

- 支持参数
    - host: 内部节点IP
    - user: 内部节点用户名
    - password: 内部节点密码
    - command: 执行命令
    - os_type: 操作系统类型（linux/windows）

- 错误码与说明详见 [docs/error_codes.md](docs/error_codes.md)

## 日志与审计

- 所有操作请求、参数、命令、结果、来源IP、时间等均详细记录于 `logs/` 目录。
- 日志分级（INFO/WARN/ERROR），支持按需查询。
- 关键操作具备审计追踪能力，便于合规与溯源。

## 安全与认证

- API接口需认证（建议支持Token/JWT/OAuth2等）。
- 支持用户、角色、权限粒度的命令与节点访问控制。
- 关键操作建议二次确认或多因子认证。

## 扩展性设计

- 支持多操作系统（当前聚焦Linux，后续可扩展Windows等）。
- 操作系统相关逻辑采用策略/工厂模式，便于扩展。
- 资源清理机制：定期清理ansible临时文件、日志、缓存，防止磁盘占满。

## 贡献指南

1. Fork本仓库并新建分支
2. 提交PR前请确保通过所有测试
3. 详细描述变更内容及动机

## License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。