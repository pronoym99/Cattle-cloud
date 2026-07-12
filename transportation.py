import os
from datetime import datetime

from sqlalchemy import create_engine, text


def log_transportation_event(
    livestock_id, transporter_user_id, destination_address, transported_at=None
):
    engine = create_engine(
        os.getenv('DATABASE_URL', 'sqlite:///cattle_cloud.db'),
        future=True,
    )
    event_time = transported_at or datetime.utcnow().isoformat()

    with engine.begin() as connection:
        connection.execute(
            text(
                'insert into transportation (livestock_id, transporter_user_id, destination_address, transported_at) '
                'values (:livestock_id, :transporter_user_id, :destination_address, :transported_at)'
            ),
            {
                'livestock_id': livestock_id,
                'transporter_user_id': transporter_user_id,
                'destination_address': destination_address,
                'transported_at': event_time,
            },
        )