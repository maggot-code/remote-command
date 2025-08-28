from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RemoteCallSerializer
from .executor import (
    confirm_port, confirm_host_pattern, confirm_public_template,
    confirm_os_template, build_inventory, build_command,
    build_script, execute_ansble, extract_result
)


class RemoteCallView(APIView):
    """
    RemoteCallView 用于远程命令执行 API。
    接收主机信息和命令参数，调用 Ansible 执行命令或脚本，并返回执行结果。
    
    请求参数：
        - os_type: 操作系统类型(linux/windows)
        - ip: 目标主机 IP 地址
        - username: 登录用户名
        - password: 登录密码(可选)
        - port: 端口号(可选)
        - command: 要执行的命令(可选)
        - file_path: 要执行的脚本路径(可选)
    返回：
        - status: 执行状态(success/error)
        - data: 执行结果数据
        - error: 错误信息
    """
    def post(self, request):
        """
        处理远程命令执行请求。
        校验参数，构建 Ansible 任务，执行并返回结果。
        """
        serializer = RemoteCallSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "data": None,
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        port = confirm_port(data["os_type"], data.get("password"), data.get("port"))
        host_pattern = confirm_host_pattern(data["os_type"])
        public_temp = confirm_public_template(data["os_type"])
        os_temp = confirm_os_template(data["os_type"], port)

        inventory, build_close = build_inventory(
            host_pattern, public_temp, os_temp, {
                "ip": data["ip"],
                "username": data["username"],
                "password": data.get("password"),
                "port": port
            }
        )

        tasks = []
        if data.get("command"):
            tasks.append(build_command(inventory, host_pattern, data["command"], os_type=data["os_type"]))
        if data.get("file_path"):
            tasks.append(build_script(inventory, host_pattern, data["file_path"], os_type=data["os_type"]))

        exec_result = execute_ansble(tasks)
        final_result = extract_result(exec_result)

        build_close()

        http_status = status.HTTP_200_OK if final_result["status"] == "success" else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(final_result, status=http_status)
