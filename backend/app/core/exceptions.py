"""Application-level exception types."""


class MuseumGuideError(Exception):
    """Base error for all museum guide exceptions."""


class VisitorNotFoundError(MuseumGuideError):
    """Raised when a visitor record cannot be found."""


class ExhibitNotFoundError(MuseumGuideError):
    """Raised when an exhibit record cannot be found."""


class GalleryNotFoundError(MuseumGuideError):
    """Raised when a gallery record cannot be found."""


class VisitNotFoundError(MuseumGuideError):
    """Raised when a visit session cannot be found."""


class PlanningError(MuseumGuideError):
    """Raised when route planning fails to produce a valid result."""


class RAGError(MuseumGuideError):
    """Raised when retrieval-augmented generation fails."""


class MemoryError(MuseumGuideError):
    """Raised when visitor memory operations fail."""


class AgentError(MuseumGuideError):
    """Raised when an agent execution fails."""


class OrchestrationError(MuseumGuideError):
    """Raised when the orchestrator cannot coordinate agents."""
