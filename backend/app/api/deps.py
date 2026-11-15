"""FastAPI dependency injection helpers."""

from app.memory.visitor_memory import VisitorMemoryService
from app.services.visit_service import VisitService
from app.services.evaluation_service import EvaluationService

# Singletons (no DB in demo mode)
_memory_service = VisitorMemoryService(db=None)
_visit_service = VisitService(db=None)
_eval_service = EvaluationService(db=None)


def get_memory_service() -> VisitorMemoryService:
    return _memory_service


def get_visit_service() -> VisitService:
    return _visit_service


def get_evaluation_service() -> EvaluationService:
    return _eval_service
