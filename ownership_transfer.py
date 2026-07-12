import os
from datetime import datetime

from dotenv import load_dotenv
from pytz import timezone
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from twilio.rest import Client

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    userid = Column(Integer, primary_key=True)
    phone = Column(Integer, nullable=False)
    address = Column(String(50), nullable=False)


class Registration(Base):
    __tablename__ = 'registration'

    regid = Column(Integer, primary_key=True)
    userid = Column(Integer, nullable=False)
    livestockid = Column(Integer, nullable=False)


class Livestock(Base):
    __tablename__ = 'livestock'

    livestockid = Column(Integer, primary_key=True)
    address = Column(String(50), nullable=False)


class Transaction(Base):
    __tablename__ = 'transactions'

    txnid = Column(Integer, primary_key=True, autoincrement=True)
    txntime = Column(String, nullable=False)
    txnstatus = Column(Boolean, nullable=False)
    regid = Column(Integer, nullable=False)
    seller_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, nullable=False)
    livestock_id = Column(Integer, nullable=False)


def check_if_exists(db_session: Session, seller_id, customer_id, livestock_id):
    if seller_id == customer_id:
        return False

    return (
        db_session.query(Registration)
        .filter(
            Registration.userid == seller_id,
            Registration.livestockid == livestock_id,
        )
        .first()
        is not None
    )


def execute_transaction(db_session: Session, seller_id, customer_id, *livestock_ids):
    indian = timezone('Asia/Kolkata')

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    global_comm_phone = os.getenv('TWILIO_GLOBAL_MSG_PHONE')
    authority_phone = os.getenv('GOVT_AUTHORITY_PHONE')
    client = Client(account_sid, auth_token)

    for livestock_id in livestock_ids:
        users = (
            db_session.query(User)
            .filter(User.userid.in_([seller_id, customer_id]))
            .all()
        )
        user_map = {user.userid: user for user in users}
        if seller_id not in user_map or customer_id not in user_map:
            continue

        sell_phone = f'+91{user_map[seller_id].phone}'
        cust_phone = f'+91{user_map[customer_id].phone}'

        registration = (
            db_session.query(Registration)
            .filter(
                Registration.userid == seller_id,
                Registration.livestockid == livestock_id,
            )
            .first()
        )
        regid_to_affect = registration.regid if registration else 0

        transaction_possibility = check_if_exists(
            db_session, seller_id, customer_id, livestock_id
        )

        if transaction_possibility:
            db_session.add(
                Transaction(
                    txntime=str(datetime.now().astimezone(indian)),
                    txnstatus=True,
                    regid=regid_to_affect,
                    seller_id=seller_id,
                    customer_id=customer_id,
                    livestock_id=livestock_id,
                )
            )

            if registration is not None:
                registration.userid = customer_id

            customer_user = user_map[customer_id]
            livestock = db_session.get(Livestock, livestock_id)
            if livestock is not None:
                livestock.address = customer_user.address

            db_session.commit()

            transact_success_msg_body = (
                f'Successful: Ownership of livestock id {livestock_id} transferred from '
                f'user id {seller_id} to user id {customer_id} at {datetime.now().astimezone(indian)}.'
            )
            message_to_authority = client.messages.create(
                body=transact_success_msg_body,
                from_=global_comm_phone,
                to=authority_phone,
            )
            print(message_to_authority.sid)

            sell_success_msg_body = (
                f'Ownership of livestock id {livestock_id} has been transferred to user id {customer_id} '
                'from your account'
            )
            message_to_seller = client.messages.create(
                body=sell_success_msg_body, from_=global_comm_phone, to=sell_phone
            )
            print(message_to_seller.sid)

            cust_success_msg_body = (
                f'Ownership of livestock id {livestock_id} received from user id {seller_id}'
            )
            message_to_customer = client.messages.create(
                body=cust_success_msg_body, from_=global_comm_phone, to=cust_phone
            )
            print(message_to_customer.sid)
        else:
            db_session.add(
                Transaction(
                    txntime=str(datetime.now().astimezone(indian)),
                    txnstatus=False,
                    regid=regid_to_affect,
                    seller_id=seller_id,
                    customer_id=customer_id,
                    livestock_id=livestock_id,
                )
            )
            db_session.commit()

            sell_fail_msg_body = (
                f"Failed: Ownership transferr of livestock id {livestock_id} from your account couldn't be "
                'carried out successfully. Refer website for details.'
            )
            message_to_seller = client.messages.create(
                body=sell_fail_msg_body, from_=global_comm_phone, to=sell_phone
            )
            print(message_to_seller.sid)


if __name__ == '__main__':
    load_dotenv()
    engine = create_engine(
        os.getenv('DATABASE_URL', 'sqlite:///cattle_cloud.db'),
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    with SessionLocal() as conn:
        pass
