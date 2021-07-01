import sqlite3
from datetime import datetime
from pytz import timezone

conn = sqlite3.connect(r'D:\PRONOY\prototype.db')
indian = timezone('Asia/Kolkata')


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

    # Figure out which registration id will be changing irrespective of transaction status
    for row in sql_connector.execute('select regid from registration where userid={} and livestockid={}'.format(seller_id, livestock_id)):
      regid_to_affect = row[0]

    if check_if_exists(sql_connector, seller_id, customer_id, livestock_id):

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
      addr_change_to_execute = 'update livestock set address="{}" where livestockid=301'.format(
          addr)
      sql_connector.execute(addr_change_to_execute)

      # Start informing the concerned parties

    else:

      # Create a log in the transaction table even if the transaction is bound to fail
      fail_txn_to_execute = 'insert into transactions (txntime, txnstatus, regid, seller_id, customer_id, livestock_id) values("{}","{}","{}","{}","{}","{}")'.format(
          txn_time, 'false', regid_to_affect, seller_id, customer_id, livestock_id)
      sql_connector.execute(fail_txn_to_execute)

      # Start informing the concerned parties
