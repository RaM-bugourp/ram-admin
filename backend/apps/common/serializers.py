from rest_framework import serializers

class StrictSerializer(serializers.Serializer):
    def to_internal_value(self,data):
        if not isinstance(data,dict):raise serializers.ValidationError({'non_field_errors':['需要JSON对象']})
        if set(data)-set(self.fields):raise serializers.ValidationError({'non_field_errors':['包含不支持的字段']})
        return super().to_internal_value(data)
