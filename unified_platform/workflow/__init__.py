"""
Platform Workflow Engine — Template-based workflow orchestration with
step dependency resolution and execution tracking.

Phase 19: Workflow Engine
Constitution: Principle 3 (Service Boundary Enforcement),
              Principle 9 (Event-Driven Readiness),
              Principle 16 (Measurable Engineering)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class WorkflowStatus(Enum):
    """Lifecycle status of a workflow instance."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Lifecycle status of an individual workflow step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ============================================================================
# Data Contracts
# ============================================================================

@dataclass
class WorkflowStep:
    """A single executable step within a workflow template."""
    step_id: str
    name: str
    description: str
    action: str
    status: StepStatus = StepStatus.PENDING
    order: int = 0
    dependencies: list[str] = field(default_factory=list)


@dataclass
class WorkflowTemplate:
    """A reusable workflow definition containing ordered steps."""
    template_id: str
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowInstance:
    """A runtime instance of a workflow template."""
    instance_id: str
    template_id: str
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    current_step: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


# ============================================================================
# Workflow Engine
# ============================================================================

class WorkflowEngine:
    """Manages workflow templates and their runtime instances.

    Provides template CRUD, instance lifecycle management, step
    completion/failure tracking, and workflow reporting.
    """

    def __init__(self) -> None:
        self._templates: dict[str, WorkflowTemplate] = {}
        self._instances: dict[str, WorkflowInstance] = {}
        self._instance_steps: dict[str, dict[str, WorkflowStep]] = {}  # instance_id -> {step_id -> step}

    def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        steps: list[WorkflowStep],
    ) -> WorkflowTemplate:
        """Create a new workflow template.

        Args:
            template_id: Unique identifier for the template.
            name: Human-readable template name.
            description: Description of the workflow purpose.
            steps: Ordered list of steps in the template.

        Returns:
            The created WorkflowTemplate.
        """
        template = WorkflowTemplate(
            template_id=template_id,
            name=name,
            description=description,
            steps=steps,
        )
        self._templates[template_id] = template
        return template

    def get_template(self, template_id: str) -> WorkflowTemplate | None:
        """Retrieve a template by ID."""
        return self._templates.get(template_id)

    def list_templates(self) -> list[WorkflowTemplate]:
        """Return all registered templates."""
        return list(self._templates.values())

    def start_workflow(
        self, instance_id: str, template_id: str
    ) -> WorkflowInstance | None:
        """Create a new workflow instance from a template.

        The first step with no unmet dependencies becomes the current step.

        Args:
            instance_id: Unique identifier for the instance.
            template_id: The template to instantiate.

        Returns:
            The created WorkflowInstance, or None if the template doesn't exist.
        """
        template = self._templates.get(template_id)
        if template is None:
            return None

        instance = WorkflowInstance(
            instance_id=instance_id,
            template_id=template_id,
        )

        step_copies = [
            WorkflowStep(
                step_id=s.step_id,
                name=s.name,
                description=s.description,
                action=s.action,
                status=StepStatus.PENDING,
                order=s.order,
                dependencies=list(s.dependencies),
            )
            for s in template.steps
        ]

        self._instance_steps[instance_id] = {s.step_id: s for s in step_copies}

        ready_steps = [
            s for s in step_copies
            if not s.dependencies
        ]
        if ready_steps:
            ready_steps.sort(key=lambda s: s.order)
            instance.current_step = ready_steps[0].step_id

        self._instances[instance_id] = instance
        return instance

    def complete_step(self, instance_id: str, step_id: str) -> bool:
        """Mark a step as completed and advance to the next eligible step.

        Args:
            instance_id: The running workflow instance.
            step_id: The step to complete.

        Returns:
            True if the step was completed and the workflow advanced.
        """
        instance = self._instances.get(instance_id)
        if instance is None or instance.status != WorkflowStatus.ACTIVE:
            return False

        steps = self._instance_steps.get(instance_id, {})
        step = steps.get(step_id)
        if step is None or step.status != StepStatus.PENDING:
            return False

        step.status = StepStatus.COMPLETED
        instance.history.append({
            "step_id": step_id,
            "action": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        })

        next_step = self._find_next_step(instance_id)
        if next_step is not None:
            instance.current_step = next_step.step_id
        else:
            instance.current_step = ""
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.utcnow()

        return True

    def fail_step(self, instance_id: str, step_id: str, reason: str = "") -> bool:
        """Mark a step as failed and transition the instance to FAILED.

        Args:
            instance_id: The running workflow instance.
            step_id: The step that failed.
            reason: Optional failure reason.

        Returns:
            True if the step was failed successfully.
        """
        instance = self._instances.get(instance_id)
        if instance is None or instance.status != WorkflowStatus.ACTIVE:
            return False

        steps = self._instance_steps.get(instance_id, {})
        step = steps.get(step_id)
        if step is None or step.status != StepStatus.PENDING:
            return False

        step.status = StepStatus.FAILED
        instance.status = WorkflowStatus.FAILED
        instance.completed_at = datetime.utcnow()
        instance.history.append({
            "step_id": step_id,
            "action": "failed",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return True

    def get_instance(self, instance_id: str) -> WorkflowInstance | None:
        """Retrieve a workflow instance by ID."""
        return self._instances.get(instance_id)

    def list_instances(
        self,
        template_id: str | None = None,
        status: WorkflowStatus | None = None,
    ) -> list[WorkflowInstance]:
        """List instances with optional filters."""
        instances = list(self._instances.values())
        if template_id is not None:
            instances = [i for i in instances if i.template_id == template_id]
        if status is not None:
            instances = [i for i in instances if i.status == status]
        return instances

    def get_workflow_report(self) -> dict[str, Any]:
        """Return a summary report of all workflow activity.

        Returns:
            Dictionary with template/instance counts and status breakdowns.
        """
        instances = list(self._instances.values())
        return {
            "total_templates": len(self._templates),
            "total_instances": len(instances),
            "instances_by_status": {
                ws.value: sum(1 for i in instances if i.status == ws)
                for ws in WorkflowStatus
            },
            "steps_by_status": {
                ss.value: sum(
                    1
                    for steps in self._instance_steps.values()
                    for s in steps.values()
                    if s.status == ss
                )
                for ss in StepStatus
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_next_step(self, instance_id: str) -> WorkflowStep | None:
        """Find the next step whose dependencies are all completed."""
        steps = self._instance_steps.get(instance_id, {})

        candidates = [
            s for s in steps.values()
            if s.status == StepStatus.PENDING
        ]

        for candidate in sorted(candidates, key=lambda s: s.order):
            deps_met = all(
                steps[dep].status == StepStatus.COMPLETED
                for dep in candidate.dependencies
                if dep in steps
            )
            if deps_met:
                return candidate

        return None


__all__ = [
    "WorkflowStatus",
    "StepStatus",
    "WorkflowStep",
    "WorkflowTemplate",
    "WorkflowInstance",
    "WorkflowEngine",
]
