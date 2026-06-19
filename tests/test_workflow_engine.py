
from unified_platform.workflow import (
    StepStatus,
    WorkflowEngine,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTemplate,
)


class TestEnums:
    def test_workflow_status_values(self):
        assert WorkflowStatus.DRAFT.value == "draft"
        assert WorkflowStatus.ACTIVE.value == "active"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"

    def test_step_status_values(self):
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_PROGRESS.value == "in_progress"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"


class TestDataclasses:
    def test_step_defaults(self):
        s = WorkflowStep(step_id="s1", name="Step 1", description="desc", action="do_thing")
        assert s.status == StepStatus.PENDING
        assert s.order == 0
        assert s.dependencies == []

    def test_template_defaults(self):
        t = WorkflowTemplate(template_id="t1", name="Tpl", description="desc")
        assert t.steps == []
        assert t.version == 1

    def test_instance_defaults(self):
        i = WorkflowInstance(instance_id="i1", template_id="t1")
        assert i.status == WorkflowStatus.ACTIVE
        assert i.current_step == ""
        assert i.completed_at is None
        assert i.history == []


class TestWorkflowEngine:
    def _engine(self):
        return WorkflowEngine()

    def _steps(self):
        return [
            WorkflowStep(step_id="s1", name="Init", description="Initialize", action="init", order=0),
            WorkflowStep(step_id="s2", name="Process", description="Process data", action="process", order=1),
            WorkflowStep(step_id="s3", name="Finalize", description="Finalize", action="finalize", order=2),
        ]

    def test_create_template(self):
        engine = self._engine()
        t = engine.create_template("t1", "Onboarding", "Employee onboarding", self._steps())
        assert t.template_id == "t1"
        assert t.name == "Onboarding"
        assert len(t.steps) == 3

    def test_get_template(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        assert engine.get_template("t1") is not None
        assert engine.get_template("missing") is None

    def test_list_templates(self):
        engine = self._engine()
        engine.create_template("t1", "A", "D", [])
        engine.create_template("t2", "B", "D", [])
        assert len(engine.list_templates()) == 2

    def test_start_workflow(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        inst = engine.start_workflow("i1", "t1")
        assert inst is not None
        assert inst.instance_id == "i1"
        assert inst.template_id == "t1"
        assert inst.status == WorkflowStatus.ACTIVE
        assert inst.current_step == "s1"

    def test_start_workflow_missing_template(self):
        engine = self._engine()
        assert engine.start_workflow("i1", "nope") is None

    def test_start_workflow_dependencies(self):
        engine = self._engine()
        steps = [
            WorkflowStep(step_id="a", name="A", description="", action="a", order=0),
            WorkflowStep(step_id="b", name="B", description="", action="b", order=1, dependencies=["a"]),
            WorkflowStep(step_id="c", name="C", description="", action="c", order=2, dependencies=["b"]),
        ]
        engine.create_template("t1", "T", "D", steps)
        inst = engine.start_workflow("i1", "t1")
        assert inst.current_step == "a"

    def test_complete_step_advances(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        assert engine.complete_step("i1", "s1") is True
        inst = engine.get_instance("i1")
        assert inst.current_step == "s2"
        assert inst.history[-1]["step_id"] == "s1"

    def test_complete_all_steps(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        engine.complete_step("i1", "s1")
        engine.complete_step("i1", "s2")
        engine.complete_step("i1", "s3")
        inst = engine.get_instance("i1")
        assert inst.status == WorkflowStatus.COMPLETED
        assert inst.current_step == ""
        assert inst.completed_at is not None

    def test_complete_step_wrong_status(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        engine.complete_step("i1", "s1")
        assert engine.complete_step("i1", "s1") is False

    def test_complete_step_nonexistent_instance(self):
        engine = self._engine()
        assert engine.complete_step("nope", "s1") is False

    def test_fail_step(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        assert engine.fail_step("i1", "s1", "timeout") is True
        inst = engine.get_instance("i1")
        assert inst.status == WorkflowStatus.FAILED
        assert inst.completed_at is not None
        assert inst.history[-1]["reason"] == "timeout"

    def test_fail_step_already_completed(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        engine.complete_step("i1", "s1")
        assert engine.fail_step("i1", "s1") is False

    def test_fail_step_nonexistent_instance(self):
        engine = self._engine()
        assert engine.fail_step("nope", "s1") is False

    def test_get_instance(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        assert engine.get_instance("i1") is not None
        assert engine.get_instance("missing") is None

    def test_list_instances_all(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        engine.start_workflow("i2", "t1")
        assert len(engine.list_instances()) == 2

    def test_list_instances_by_template(self):
        engine = self._engine()
        engine.create_template("t1", "A", "D", [])
        engine.create_template("t2", "B", "D", [])
        engine.start_workflow("i1", "t1")
        engine.start_workflow("i2", "t2")
        t1_insts = engine.list_instances(template_id="t1")
        assert len(t1_insts) == 1
        assert t1_insts[0].instance_id == "i1"

    def test_list_instances_by_status(self):
        engine = self._engine()
        engine.create_template("t1", "T", "D", self._steps())
        engine.start_workflow("i1", "t1")
        engine.start_workflow("i2", "t1")
        engine.complete_step("i1", "s1")
        engine.complete_step("i1", "s2")
        engine.complete_step("i1", "s3")
        completed = engine.list_instances(status=WorkflowStatus.COMPLETED)
        assert len(completed) == 1
        active = engine.list_instances(status=WorkflowStatus.ACTIVE)
        assert len(active) == 1

    def test_workflow_report_empty(self):
        report = self._engine().get_workflow_report()
        assert report["total_templates"] == 0
        assert report["total_instances"] == 0

    def test_workflow_report_populated(self):
        engine = self._engine()
        engine.create_template("t1", "A", "D", self._steps())
        engine.create_template("t2", "B", "D", [])
        engine.start_workflow("i1", "t1")
        engine.start_workflow("i2", "t1")
        engine.complete_step("i1", "s1")
        engine.complete_step("i1", "s2")
        engine.complete_step("i1", "s3")
        engine.fail_step("i2", "s1", "error")
        report = engine.get_workflow_report()
        assert report["total_templates"] == 2
        assert report["total_instances"] == 2
        assert report["instances_by_status"]["completed"] == 1
        assert report["instances_by_status"]["failed"] == 1
        assert report["steps_by_status"]["completed"] == 3
        assert report["steps_by_status"]["failed"] == 1

    def test_dependency_chain_execution(self):
        engine = self._engine()
        steps = [
            WorkflowStep(step_id="a", name="A", description="", action="a", order=0),
            WorkflowStep(step_id="b", name="B", description="", action="b", order=1, dependencies=["a"]),
            WorkflowStep(step_id="c", name="C", description="", action="c", order=2, dependencies=["a", "b"]),
        ]
        engine.create_template("t1", "T", "D", steps)
        engine.start_workflow("i1", "t1")
        engine.complete_step("i1", "a")
        assert engine.get_instance("i1").current_step == "b"
        engine.complete_step("i1", "b")
        assert engine.get_instance("i1").current_step == "c"
        engine.complete_step("i1", "c")
        assert engine.get_instance("i1").status == WorkflowStatus.COMPLETED
