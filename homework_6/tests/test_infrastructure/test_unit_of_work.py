import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class TestSqlAlchemyUnitOfWork:

    def test_should_call_commit_on_session(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        uow = SqlAlchemyUnitOfWork(mock_session)

        uow.commit()

        assert mock_session.commit.call_count == 1

    def test_should_call_rollback_on_session(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        uow = SqlAlchemyUnitOfWork(mock_session)

        uow.rollback()

        assert mock_session.rollback.call_count == 1

    def test_should_commit_and_close_on_context_manager_success(
        self, mocker: MockerFixture
    ):
        mock_session = mocker.Mock(spec=Session)
        uow = SqlAlchemyUnitOfWork(mock_session)

        with uow:
            pass

        assert (
            mock_session.commit.call_count,
            mock_session.rollback.call_count,
            mock_session.close.call_count,
        ) == (1, 0, 1)

    def test_should_rollback_and_close_on_context_manager_exception(
        self, mocker: MockerFixture
    ):
        mock_session = mocker.Mock(spec=Session)
        uow = SqlAlchemyUnitOfWork(mock_session)

        with pytest.raises(ValueError):
            with uow:
                raise ValueError("Test exception")

        assert (
            mock_session.rollback.call_count,
            mock_session.commit.call_count,
            mock_session.close.call_count,
        ) == (1, 0, 1)
