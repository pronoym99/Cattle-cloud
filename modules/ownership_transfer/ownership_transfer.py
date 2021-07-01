from datetime import datetime
from pytz import timezone
from twilio.rest import Client
import os

# Always use .env files for storing sensitive information for a given project instance
from dotenv import load_dotenv
load_dotenv()

# Set timezone for later use
indian = timezone('Asia/Kolkata')

# Connect to your database
conn = sqlite3.connect(r'D:\PRONOY\prototype.db')



def check_if_exists(sql_connector, seller_id, customer_id, livestock_id):
  if seller_id == customer_id:
    return False
  else:
    # Customer may be buying cattle for the very first time so need to check for a valid mapping in the registration table
    sell_check_to_execute = 'select exists(select regid from registration where userid = {} and livestockid={})'.format(
        seller_id, livestock_id)
    for row in sql_connector.execute(sell_check_to_execute):
      flag = row[0]

    if flag:
      return True
    else:
      return False


def execute_transaction(sql_connector, seller_id, customer_id, *livestock_ids):
  for livestock_id in livestock_ids:

    # Do your Twilio configuration here
    # Load variables from .env file only
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    global_comm_phone = os.getenv('TWILIO_GLOBAL_MSG_PHONE')
    authority_phone = os.getenv('GOVT_AUTHORITY_PHONE')
    client = Client(account_sid, auth_token)

    # First obtain phone nos. of both the parties
    rows = sql_connector.execute(
        'select phone from user where userid={} or userid={}'.format(seller_id, customer_id)).fetchall()
    sell_phone, cust_phone = '+91{}'.format(
        rows[0][0]), '+91{}'.format(rows[1][0])

    regid_to_affect = 0
    # Figure out which registration id will be changing irrespective of transaction status
    for row in sql_connector.execute('select regid from registration where userid={} and livestockid={}'.format(seller_id, livestock_id)):
      regid_to_affect = row[0]

    transaction_possibility = check_if_exists(
        sql_connector, seller_id, customer_id, livestock_id)

    if transaction_possibility:

      # Create a log in the transaction table

      success_txn_to_execute = 'insert into transactions (txntime, txnstatus, regid, seller_id, customer_id, livestock_id) values("{}","{}","{}","{}","{}","{}")'.format(
          datetime.now().astimezone(indian), 'true', regid_to_affect, seller_id, customer_id, livestock_id)
      sql_connector.execute(success_txn_to_execute)

      # Change the userid in the registration table for the same livestockid
      user_change_to_execute = 'update registration set userid="{}" where userid="{}" and livestockid="{}"'.format(
          customer_id, seller_id, livestock_id)
      sql_connector.execute(user_change_to_execute)

      # Change the livestock_id's address to that of the customer_id
      for row in conn.execute('select address from user where userid={}'.format(customer_id)):
        addr = row[0]
      addr_change_to_execute = 'update livestock set address="{}" where livestockid="{}"'.format(
          addr, livestock_id)
      sql_connector.execute(addr_change_to_execute)

      # Start informing the concerned parties
      # Inform the Governing authority and the customer only if the transaction is successful
      # Inform the seller nonetheless
      # Print message sids to indicate transaction success

      transact_success_msg_body = 'Successful: Ownership of livestock id {} transferred from user id {} to user id {} at {}.'.format(
          livestock_id, seller_id, customer_id, datetime.now().astimezone(indian))
      message_to_authority = client.messages.create(
          body=transact_success_msg_body, from_=global_comm_phone, to=authority_phone)
      print(message_to_authority.sid)

      sell_success_msg_body = 'Ownership of livestock id {} has been transferred to user id {} from your account'.format(
          livestock_id, customer_id)
      message_to_seller = client.messages.create(
          body=sell_success_msg_body, from_=global_comm_phone, to=sell_phone)
      print(message_to_seller.sid)

      cust_success_msg_body = 'Ownership of livestock id {} received from user id {}'.format(
          livestock_id, seller_id)
      message_to_customer = client.messages.create(
          body=cust_success_msg_body, from_=global_comm_phone, to=cust_phone)
      print(message_to_customer.sid)

    else:

      # Create a log in the transaction table even if the transaction is bound to fail
      fail_txn_to_execute = 'insert into transactions (txntime, txnstatus, regid, seller_id, customer_id, livestock_id) values("{}","{}","{}","{}","{}","{}")'.format(
          datetime.now().astimezone(indian), 'false', regid_to_affect, seller_id, customer_id, livestock_id)
      sql_connector.execute(fail_txn_to_execute)

      # Start informing the concerned parties
      # Inform the Governing authority and the customer only if the transaction is successful
      # Inform the seller nonetheless
      # Print message sids to indicate transaction success

      sell_fail_msg_body = "Failed: Ownership transferr of livestock id {} from your account couldn't be carried out successfully. Refer website for details.".format(
          livestock_id)
      message_to_seller = client.messages.create(
          body=sell_fail_msg_body, from_=global_comm_phone, to=sell_phone)
      print(message_to_seller.sid)
