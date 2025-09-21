# Ansible跳板机免密

## 环境:
1. Django Server(192.168.199.196)
    * private key: /root/.ssh/id_rsa_ansible
    * public key: /root/.ssh/id_rsa_ansible.pub
2. 堡垒机(192.168.27.131)
    * user: root
    * password: 123
    * private key: /root/.ssh/id_rsa
    * publick key: /root/.ssh/id_rsa.pub
    * authorized_keys: /root/.ssh/authorized_keys
3. 内网节点(192.168.27.132)
    * user: internal-node
    * password: 123
    * authorized_keys: /home/internal-node/.ssh/authorized_keys

## 版本:
1. Python: 3.9.6
2. Django: 4.2.23
3. Ansible: 8.7.0
4. Ansible-runner: 2.4.1
5. OpenSSH:
    5.1 Django Server: OpenSSH_9.9p2, LibreSSL 3.3.6
    5.2 堡垒机: OpenSSH_8.7p1, OpenSSL 3.2.2 4 Jun 2024
    5.3 内网节点: OpenSSH_8.7p1, OpenSSL 3.2.2 4 Jun 2024

## 架构:
1. Django Server与内网节点无法互通
2. Django Server使用/root/.ssh/id_rsa_ansible对堡垒机免密
3. 堡垒机使用/root/.ssh/id_rsa对内部节点免密

## 需求:
1. Django Server提供一个对外可以访问的接口用于接收用户提供的信息:
    1.1 内部节点IP
    1.2 内部节点用户
    1.3 内部节点密码
    1.4 内部节点上执行的命令
    1.5 内部系统类型（linux or windows）
2. Django Server整合用户提供的信息之后组装成为一个ansible上下文，提供给ansible_runner.run函数用于调用ansible执行
3. Django Server中堡垒机的相关信息以配置文件的方式保存
4. ansible首先会经过堡垒机，然后由堡垒机将流量转发到内部节点，最终在内部节点执行用户提供的命令，然后将结果返回到堡垒机，再由堡垒机返回到Django Server最终返回给用户完整整个业务流程

## 设计补充

### 1. 日志与审计
* 所有操作请求、参数、执行命令、结果、来源IP、时间等需详细记录。
* 日志建议分级（INFO/WARN/ERROR），并支持按需查询。
* 关键操作（如命令执行、配置变更）需有审计追踪，便于合规和溯源。

### 2. 结果回传与格式
* 统一API返回格式，建议结构：
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
* 便于前端或调用方自动化处理和展示。

### 3. 支持多种操作系统
* 当前聚焦Linux节点，后续可扩展Windows等其他系统。
* 建议抽象操作系统相关逻辑，采用策略模式或工厂模式，便于后续扩展。
* 例如：
    - `LinuxExecutor`、`WindowsExecutor`等实现统一接口。
    - 命令模板、参数组装、结果解析等均可按操作系统定制。

### 4. 资源清理
* ansible执行后产生的临时文件、日志、缓存等需定期清理。
* 可通过定时任务（如crontab）或在业务流程结束后自动清理。
* 防止磁盘空间被占满，提升系统稳定性。

### 5. 错误处理
* 对ansible_runner、SSH连接、参数校验等各环节的异常需有完善的捕获和处理。
* API返回需明确错误码和错误信息，便于定位问题。
* 建议对常见错误场景（如连接超时、认证失败、命令执行失败等）有专门的错误码和文档说明。

### 6. 认证与授权
* 对外API需加认证（如Token、JWT、OAuth2等），防止未授权访问。
* 可按用户、角色、权限粒度控制可执行的命令和可访问的节点。
* 关键操作建议二次确认或多因子认证，提升安全性。