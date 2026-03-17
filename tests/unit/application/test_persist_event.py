"""Tests for PersistEvent use case."""

from bank_ingest.application.use_cases.persist_event import PersistEvent
from bank_ingest.domain.entities import FinancialEvent
from unit.application.fakes import FakeEventRepository, FakeLogger


class TestPersistEvent:
    def test_saves_new_event(self, financial_event: FinancialEvent) -> None:
        repo = FakeEventRepository()
        use_case = PersistEvent(repository=repo, logger=FakeLogger())

        use_case.execute(financial_event)

        assert repo.find_by_id(financial_event.id) == financial_event

    def test_skips_duplicate_event(self, financial_event: FinancialEvent) -> None:
        repo = FakeEventRepository(existing_ids={financial_event.id.value})
        logger = FakeLogger()
        use_case = PersistEvent(repository=repo, logger=logger)

        use_case.execute(financial_event)

        # Should not be saved again (existing_ids pre-populated, events dict empty)
        assert repo.find_by_id(financial_event.id) is None
        assert len(logger.warnings) > 0

    def test_logs_warning_on_duplicate(self, financial_event: FinancialEvent) -> None:
        repo = FakeEventRepository(existing_ids={financial_event.id.value})
        logger = FakeLogger()
        use_case = PersistEvent(repository=repo, logger=logger)

        use_case.execute(financial_event)

        assert any(
            "duplicate" in w.lower() or "exists" in w.lower() for w in logger.warnings
        )

    def test_saves_event_with_correct_id(self, financial_event: FinancialEvent) -> None:
        repo = FakeEventRepository()
        use_case = PersistEvent(repository=repo, logger=FakeLogger())

        use_case.execute(financial_event)

        saved = repo.find_by_id(financial_event.id)
        assert saved is not None
        assert saved.id == financial_event.id

    def test_logs_successful_save(self, financial_event: FinancialEvent) -> None:
        repo = FakeEventRepository()
        logger = FakeLogger()
        use_case = PersistEvent(repository=repo, logger=logger)

        use_case.execute(financial_event)

        assert len(logger.infos) > 0 or len(logger.debugs) > 0
