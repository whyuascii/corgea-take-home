import pytest
from django_q.models import Schedule

from core.schedules import PERIODIC_SCHEDULES, register_schedules


@pytest.mark.django_db
class TestRegisterSchedules:
    def test_creates_all_schedules(self):
        register_schedules()
        for spec in PERIODIC_SCHEDULES:
            assert Schedule.objects.filter(name=spec["name"]).exists()

    def test_idempotent_on_rerun(self):
        register_schedules()
        register_schedules()
        for spec in PERIODIC_SCHEDULES:
            assert Schedule.objects.filter(name=spec["name"]).count() == 1

    def test_updates_changed_config(self):
        # Pre-create a schedule with a different func
        Schedule.objects.create(
            name="cleanup_login_attempts",
            func="old.module.path",
            schedule_type=Schedule.WEEKLY,
            repeats=5,
        )
        register_schedules()
        sched = Schedule.objects.get(name="cleanup_login_attempts")
        assert sched.func == "accounts.tasks.cleanup_login_attempts"
        assert sched.schedule_type == Schedule.DAILY
        assert sched.repeats == -1

    def test_removes_stale_named_schedules(self):
        Schedule.objects.create(
            name="obsolete_task",
            func="old.module.obsolete",
            schedule_type=Schedule.DAILY,
            repeats=-1,
        )
        register_schedules()
        assert not Schedule.objects.filter(name="obsolete_task").exists()

    def test_preserves_unnamed_schedules(self):
        unnamed = Schedule.objects.create(
            func="some.manual.task",
            schedule_type=Schedule.HOURLY,
            repeats=-1,
        )
        register_schedules()
        assert Schedule.objects.filter(pk=unnamed.pk).exists()
