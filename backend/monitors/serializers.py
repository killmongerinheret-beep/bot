from rest_framework import serializers
from .models import Agency, MonitorTask, CheckResult, Proxy, SiteCredential

class SiteCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteCredential
        fields = '__all__'

class ProxySerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        fields = '__all__'

class AgencySerializer(serializers.ModelSerializer):
    credentials = SiteCredentialSerializer(many=True, read_only=True)
    task_limit = serializers.SerializerMethodField()

    class Meta:
        model = Agency
        fields = ['id', 'name', 'api_key', 'telegram_chat_id', 'credentials', 'created_at', 'plan', 'task_limit']

    def get_task_limit(self, obj):
        limits = {'free': 2, 'pro': 20, 'agency': 500}
        return limits.get(obj.plan, 2)

class CheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckResult
        fields = '__all__'

class MonitorTaskSerializer(serializers.ModelSerializer):
    agency_name = serializers.ReadOnlyField(source='agency.name')
    latest_check = serializers.SerializerMethodField()
    
    class Meta:
        model = MonitorTask
        fields = '__all__'
    
    def get_latest_check(self, obj):
        """Get the most recent CheckResult with slots for this task."""
        latest_result = obj.results.order_by('-check_time').first()
        if latest_result:
            return CheckResultSerializer(latest_result).data
        return None
