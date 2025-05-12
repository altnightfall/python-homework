from sqlalchemy.orm import Session
from domain.unit_of_work import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, session: Session):
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is None:
            self.commit()
        else:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
