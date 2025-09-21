from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from remote_call.utils import build_response
from remote_call.services import RemoteCallService
from .serializers import RemoteCallSerializer


class RemoteCallView(APIView):
    """
    远程命令执行 API
    - 校验参数，构建上下文，调用 Ansible 执行命令或脚本，返回标准结构结果。

    请求参数：
        os_type: 操作系统类型 (linux/windows)
        ip: 目标主机 IP
        username: 登录用户名
        password: 登录密码(可选)
        port: 端口号(可选)
        command: 要执行的命令(可选)
        file_path: 要执行的脚本路径(可选)
        use_bastion: 是否使用堡垒机(可选, 默认True)
    返回：
        status: "success"/"error"
        data: 结果数据
        error: 错误信息
        target: ansible 运行元数据
    """
    def post(self, request):
        """
        处理远程命令执行请求，返回标准结构。
        """
        serializer = RemoteCallSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                build_response(status="error", error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        service = RemoteCallService(data)

        return Response(
            build_response(**service),
            status=status.HTTP_200_OK
        )
