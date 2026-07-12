import os
from datetime import datetime

from dotenv import load_dotenv
from pytz import timezone
from sqlalchemy import create_engine, text
from twilio.rest import Client


def check_if_exists(sql_connector, seller_id, customer_id, livestock_id):
    if seller_id == customer_id:
        return False

    sell_check_to_execute = text(
        'select exists(select regid from registration where userid = :seller_id and livestockid = :livestock_id)'
    )
    flag = sql_connector.execute(
        sell_check_to_execute,
        {'seller_id': seller_id, 'livestock_id': livestock_id},
    ).scalar()
    return bool(flag)


def execute_transaction(sql_connector, seller_id, customer_id, *livestock_ids):
    indian = timezone('Asia/Kolkata')

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    global_comm_phone = os.getenv('TWILIO_GLOBAL_MSG_PHONE')
    authority_phone = os.getenv('GOVT_AUTHORITY_PHONE')
    client = Client(account_sid, auth_token)

    for livestock_id in livestock_ids:
        rows = sql_connector.execute(
            text(
                'select userid, phone from user where userid = :seller_id or userid = :customer_id'
            ),
            {'seller_id': seller_id, 'customer_id': customer_id},
        ).all()

        phone_map = {row[0]: row[1] for row in rows}
        if seller_id not in phone_map or customer_id not in phone_map:
            continue

        sell_phone = f'+91{phone_map[seller_id]}'
        cust_phone = f'+91{phone_map[customer_id]}'

        regid_to_affect = sql_connector.execute(
            text(
                'select regid from registration where userid = :seller_id and livestockid = :livestock_id'
            ),
            {'seller_id': seller_id, 'livestock_id': livestock_id},
        ).scalar()

        transaction_possibility = check_if_exists(
            sql_connector, seller_id, customer_id, livestock_id
        )

        if transaction_possibility:
            sql_connector.execute(
                text(
                    'insert into transactions (txntime, txnstatus, regid, seller_id, customer_id, livestock_id) '
                    'values(:txntime, :txnstatus, :regid, :seller_id, :customer_id, :livestock_id)'
                ),
                {
                    'txntime': str(datetime.now().astimezone(indian)),
                    'txnstatus': 'true',
                    'regid': regid_to_affect,
                    'seller_id': seller_id,
                    'customer_id': customer_id,
                    'livestock_id': livestock_id,
                },
            )

            sql_connector.execute(
                text(
                    'update registration set userid = :customer_id where userid = :seller_id and livestockid = :livestock_id'
                ),
                {
                    'customer_id': customer_id,
                    'seller_id': seller_id,
                    'livestock_id': livestock_id,
                },
            )

            addr = sql_connector.execute(
                text('select address from user where userid = :customer_id'),
                {'customer_id': customer_id},
            ).scalar()
            if addr is not None:
                sql_connector.execute(
                    text(
                        'update livestock set address = :addr where livestockid = :livestock_id'
                    ),
                    {'addr': addr, 'livestock_id': livestock_id},
                )

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
            sql_connector.execute(
                text(
                    'insert into transactions (txntime, txnstatus, regid, seller_id, customer_id, livestock_id) '
                    'values(:txntime, :txnstatus, :regid, :seller_id, :customer_id, :livestock_id)'
                ),
                {
                    'txntime': str(datetime.now().astimezone(indian)),
                    'txnstatus': 'false',
                    'regid': regid_to_affect,
                    'seller_id': seller_id,
                    'customer_id': customer_id,
                    'livestock_id': livestock_id,
                },
            )

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
    with engine.begin() as conn:
        pass
