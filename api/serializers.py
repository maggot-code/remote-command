from rest_framework import serializers

class RemoteCallSerializer(serializers.Serializer):
    """
    只负责接口层参数校验，不做任何业务逻辑。
    """
    os_type = serializers.ChoiceField(
        choices=["linux", "windows"],
        error_messages={
            "required": "OS type is required",
            "invalid_choice": "OS type must be one of [linux | windows]"
        }
    )
    ip = serializers.IPAddressField(
        error_messages={
            "required": "IP address is required",
            "invalid": "Please enter a valid IP address"
        }
    )
    username = serializers.CharField(
        error_messages={
            "required": "Username is required",
            "blank": "Username cannot be blank"
        }
    )
    password = serializers.CharField(required=False, allow_blank=True)
    port = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=65535,
        error_messages={
            "invalid": "Port must be an integer",
            "min_value": "Port cannot be less than 1",
            "max_value": "Port cannot be greater than 65535"
        }
    )
    command = serializers.CharField(required=False, allow_blank=True)
    file_path = serializers.CharField(required=False, allow_blank=True)
    use_bastion = serializers.BooleanField(required=False, default=True)
