"""
Examinations Views.
Module 6 - Results management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Score, ResultBatch, MalpracticeCase
from .serializers import ScoreSerializer, ResultBatchSerializer, MalpracticeCaseSerializer


class ScoreViewSet(viewsets.ModelViewSet):
    """Score entry and management."""
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Role-based filtering
        if user.role == "student":
            return qs.filter(student__user=user)
        elif user.role == "lecturer":
            return qs.filter(offering__lecturer__user=user)
        
        return qs


class ResultBatchViewSet(viewsets.ModelViewSet):
    """Result batch with 5-stage FSM workflow."""
    queryset = ResultBatch.objects.all()
    serializer_class = ResultBatchSerializer
    
    @action(detail=True, methods=["post"])
    def hod_approve(self, request, pk=None):
        """HOD approval step."""
        batch = self.get_object()
        batch.hod_approve(request.user)
        return Response({"status": "approved by HOD"})
    
    @action(detail=True, methods=["post"])
    def dean_approve(self, request, pk=None):
        """Dean approval step."""
        batch = self.get_object()
        batch.dean_approve(request.user)
        return Response({"status": "approved by Dean"})
    
    @action(detail=True, methods=["post"])
    def compile(self, request, pk=None):
        """Exam officer compile."""
        batch = self.get_object()
        batch.exam_officer_compile(request.user)
        return Response({"status": "compiled"})
    
    @action(detail=True, methods=["post"])
    def senate_ratify(self, request, pk=None):
        """Senate ratification."""
        batch = self.get_object()
        batch.senate_ratify(request.user)
        return Response({"status": "ratified by Senate"})
    
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish results."""
        batch = self.get_object()
        batch.publish()
        return Response({"status": "published"})


class MalpracticeCaseViewSet(viewsets.ModelViewSet):
    """Exam malpractice case management."""
    queryset = MalpracticeCase.objects.all()
    serializer_class = MalpracticeCaseSerializer