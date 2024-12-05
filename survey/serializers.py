from rest_framework import serializers

from .models import Entry, Filter
from users.models import Group

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class EntrySerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Entry
        fields = ['id', 'username', 'classification', 'csection', 'date', 'groups']
        # cursed but unsure otherwise
    def __init__(self, *args, **kwargs):
        # Remove 'groups' field if specified in context
        exclude_groups = kwargs.pop('exclude_groups', False)
        super().__init__(*args, **kwargs)
        if exclude_groups:
            self.fields.pop('groups', None)

class FilterSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Filter
        fields = ['id', 'name', 'user', 'groups']
        
class FilterIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ['id']