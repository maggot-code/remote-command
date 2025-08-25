import ansible_runner
import tempfile

def biz_execute_command(dto: dict) -> dict:
    """
    使用 ansible-runner 执行 Linux 命令
    dto: {
        ip, username, password, port, command
    }
    """
    ip = dto.get("ip")
    username = dto.get("username")
    password = dto.get("password")
    port = dto.get("port", 22)
    command = dto.get("command")

    hosts_content = f"""[linux_servers]
{ip} ansible_user={username} ansible_ssh_pass={password} ansible_port={port} ansible_connection=ssh ansible_python_interpreter=/usr/bin/python3
"""

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".ini") as f:
        f.write(hosts_content)
        hosts_path = f.name

    try:
        r = ansible_runner.run(
            private_data_dir=".",
            inventory=hosts_path,
            host_pattern="linux_servers",
            module="command",
            module_args=command,
            quiet=True
        )

        status = "success" if r.rc == 0 else "failed"
        output_lines = []
        for event in r.events:
            if event.get("event") in ["runner_on_ok", "runner_on_failed"]:
                res = event["event_data"].get("res", {})
                if "stdout" in res and res["stdout"]:
                    output_lines.append(res["stdout"])
        output = "\n".join(output_lines)

        return {
            "msg": "Linux executed",
            "ip": ip,
            "command": command,
            "status": status,
            "output": output
        }
    finally:
        # 临时文件可以先不删除，保证调试时可查
        pass

def biz_execute_command_nopwd(dto: dict) -> dict:
    """
    使用 ansible-runner 执行 Linux 命令（无密码）
    dto: {
        ip, username, port, command
    }
    """
    ip = dto.get("ip")
    username = dto.get("username")
    port = dto.get("port", 22)
    command = dto.get("command")

    hosts_content = f"""[linux_servers]
{ip} ansible_user={username} ansible_port={port} ansible_connection=ssh ansible_python_interpreter=/usr/bin/python3
"""

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".ini") as f:
        f.write(hosts_content)
        hosts_path = f.name

    try:
        r = ansible_runner.run(
            private_data_dir=".",
            inventory=hosts_path,
            host_pattern="linux_servers",
            module="command",
            module_args=command,
            quiet=True
        )

        status = "success" if r.rc == 0 else "failed"
        output_lines = []
        for event in r.events:
            if event.get("event") in ["runner_on_ok", "runner_on_failed"]:
                res = event["event_data"].get("res", {})
                if "stdout" in res and res["stdout"]:
                    output_lines.append(res["stdout"])
        output = "\n".join(output_lines)

        return {
            "msg": "Linux executed no password",
            "ip": ip,
            "command": command,
            "status": status,
            "output": output
        }
    finally:
        # 临时文件可以先不删除，保证调试时可查
        pass

def biz_script(dto:dict) -> dict:
    """
    使用 ansible-runner 执行 Linux 脚本（无密码）
    dto: {
        ip, username, port, file_path, remote_host
    }
    """
    ip = dto.get("ip")
    username = dto.get("username")
    port = dto.get("port", 22)
    local_path = dto.get("file_path")

    hosts_content = f"""[linux_servers]
{ip} ansible_user={username} ansible_port={port} ansible_connection=ssh ansible_python_interpreter=/usr/bin/python3
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".ini") as f:
        f.write(hosts_content)
        hosts_path = f.name

    try:
        r = ansible_runner.run(
            private_data_dir=".",
            inventory=hosts_path,
            host_pattern="linux_servers",
            module="script",
            module_args=local_path,
            quiet=True
        )

        status = "success" if r.rc == 0 else "failed"
        output_lines = []
        for event in r.events:
            if event.get("event") in ["runner_on_ok", "runner_on_failed"]:
                res = event["event_data"].get("res", {})
                if "stdout" in res and res["stdout"]:
                    output_lines.append(res["stdout"])
        output = "\n".join(output_lines)

        return {
            "msg": "Linux script executed",
            "ip": ip,
            "command": local_path,
            "status": status,
            "output": output
        }
    finally:
        pass
