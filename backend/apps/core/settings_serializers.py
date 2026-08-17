from rest_framework import serializers


class SettingPatchSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.JSONField()
