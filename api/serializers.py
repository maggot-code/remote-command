from rest_framework import serializers

class RemoteCallSerializer(serializers.Serializer):
    os_type = serializers.ChoiceField(choices=["linux", "windows"])
    ip = serializers.IPAddressField()
    username = serializers.CharField()
    password = serializers.CharField(required=False, allow_blank=True)
    port = serializers.IntegerField(required=False, min_value=1, max_value=65535)
    command = serializers.CharField(required=False, allow_blank=True)
    file_path = serializers.CharField(required=False, allow_blank=True)
