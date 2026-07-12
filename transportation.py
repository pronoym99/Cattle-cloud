import os
from datetime import datetime

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class TransportationEvent(Base):
    __tablename__ = 'transportation'

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    livestock_id = Column(Integer, nullable=False)
    transporter_user_id = Column(Integer, nullable=False)
    destination_address = Column(String, nullable=False)
    transported_at = Column(String, nullable=False)

def log_transportation_event(
    livestock_id, transporter_user_id, destination_address, transported_at=None
):
    engine = create_engine(
        os.getenv('DATABASE_URL', 'sqlite:///cattle_cloud.db'),
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    event_time = transported_at or datetime.utcnow().isoformat()

    with SessionLocal() as session:
        session.add(
            TransportationEvent(
                livestock_id=livestock_id,
                transporter_user_id=transporter_user_id,
                destination_address=destination_address,
                transported_at=event_time,
            )
        )
        session.commit()