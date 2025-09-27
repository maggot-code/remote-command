# Copilot Instructions for AI Coding Agents

## 项目架构与核心组件
- 本项目为 Django + Ansible 跳板机自动化命令平台，服务于堡垒机场景下的内网节点批量运维。
- 主要目录：
  - `ansible/`：Ansible 封装、配置与 Runner 调用（核心自动化逻辑）
  - `api/`：Django REST API，统一入口，参数校验、权限控制、结果格式化
  - `artifacts/`：任务执行产物、缓存，按 UUID 分目录
  - `logs/`：详细操作日志与审计，分级存储
  - `remote_call/`：远程命令上下文与调度逻辑
  - `server/`：Django 服务端主逻辑
  - `test/`：测试用例，建议 PR 前全部通过

## 关键开发流程
- 启动服务：
  ```bash
  python manage.py migrate
  python manage.py runserver 0.0.0.0:8000
  ```
- API 调用示例：
  ```http
  POST /api/remote_call/
  {
    "host": "192.168.27.132",
    "user": "internal-node",
    "command": "uname -a",
    "os_type": "linux"
  }
  ```
- 日志自动记录于 `logs/`，产物存储于 `artifacts/`，无需手动管理。

## 项目约定与模式
- API 统一返回格式，见 `README.md` 示例。
- 多层 SSH 跳转：Django Server → 堡垒机 → 内网节点，密钥路径与配置见 `ansible/config.py`。
- 操作系统相关逻辑采用策略/工厂模式，便于扩展。
- 资源清理机制建议定期清理临时文件、日志、缓存。

## 安全与认证
- API 需认证（Token/JWT/OAuth2），权限控制建议在 `api/` 层实现。
- 日志与审计详见 `logs/`，关键操作具备溯源能力。

## 贡献与扩展
- 新增操作系统支持时，建议采用策略/工厂模式扩展。
- 所有变更需通过测试，详见 `test/`。
- 详细开发流程、错误码等见 `docs/`。

---
如有不清楚的架构、流程或约定，请反馈以便补充完善。