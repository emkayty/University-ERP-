"""
Examinations Serializers.
"""

from rest_framework import serializers
from .models import Score, ResultBatch, MalpracticeCase, MalpracticePattern


class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = "__all__"
        read_only_fields = ["entered_by", "entered_at"]


class ResultBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultBatch
        fields = "__all__"


class MalpracticeCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MalpracticeCase
        fields = "__all__"


class MalpracticePatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = MalpracticePattern
        fields = "__all__"