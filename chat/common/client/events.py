# events.py
# in chat.common.client

from chat.common.operations import Opcode
from typing import Callable


def main(entry: Callable, request: Callable, handler: Callable, **kwargs):
    """A nice (TM) generic way of handling the event logic shared by the wire
       and gRPC protocols.
       `entry` is called once at the beginning, to establish the connection
        (or whatever other setup you want to do). Note that `kwargs` will be
        set to the return value of `entry` here, so it can pass the connections
        onwards to `request` and `handler`.
       `request` does requests across the connection,
       `handler` handles errors.
    """
    try:
        kwargs = entry(**kwargs)
        has_logged_in = False

        print('\n""""""""""""""""""\nWELCOME TO CHATMAN\n""""""""""""""""""\n')

        while not has_logged_in:
            print('Do you want to...\n'
                    '1) Login\n'
                    '2) Signup\n')
            opcode = input('> 1/2: ')

            if opcode not in ['1', '2']:
                continue

            # - 1 since Opcode.CREATE_ACCOUNT has value 0.
            opcode = Opcode(int(opcode) - 1)
            match opcode:
                case Opcode.LOGIN_ACCOUNT:
                    username = input('> Username: ')
                    response = request(opcode=Opcode.LOGIN_ACCOUNT,
                        username=username,
                        **kwargs)
                    if response.get_error() == '':
                        print('\nLogin succesful!\n')
                        has_logged_in = True
                    else:
                        print('\n' + response.get_error() + '\n')
                case Opcode.CREATE_ACCOUNT:
                    username = input('> Username: ')
                    response = request(opcode=Opcode.CREATE_ACCOUNT,
                        username=username,
                        **kwargs)
                    if response.get_error() == '':
                        print('\nAccount creation succesful!\n')
                        has_logged_in = True
                    else:
                        print('\n' + response.get_error() + '\n')

        while True:
            print('Do you want to...\n'
                  '1) List Accounts\n'
                  '2) Send a Message\n'
                  '3) Deliver Undelivered Messages\n'
                  '4) Delete Account\n')
            opcode = input('> 1/2/3/4: ')

            if opcode not in ['1', '2', '3', '4']:
                continue

            # + 1 since Opcode.CREATE_ACCOUNT has value 0.
            opcode = Opcode(int(opcode) + 1)
            match opcode:
                case Opcode.LIST_ACCOUNTS:
                    response = request(opcode=Opcode.LIST_ACCOUNTS,
                                       **kwargs)
                    accounts = response.get_accounts()
                    formatted_accounts = [f"{account.get_username()} (active: {account.get_logged_in()})" for account in accounts]
                    formatted_account_list = ", ".join(formatted_accounts)
                    if response.get_error() == '':
                        print('\nAccounts:\n[' + formatted_account_list + ']\n')
                    else:
                        print('\n' + response.get_error() + '\n')
                case Opcode.SEND_MESSAGE:
                    recipient = input('> Recipient: ')
                    message = input('> Message: ')
                    response = request(
                        opcode=Opcode.SEND_MESSAGE,
                        message=message,
                        recipient_username=recipient,
                        sender_username=username,
                        **kwargs)
                    if response.get_error() == '':
                        print('\nYour message was sent!\n')
                    else:
                        print('\n' + response.get_error() + '\n')
                case Opcode.DELIVER_UNDELIVERED_MESSAGES:
                    response = request(opcode=Opcode
                                       .DELIVER_UNDELIVERED_MESSAGES,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':           
                        messages = response.get_messages()
                        formatted_messages = ""

                        # Create a dictionary to group messages by sender
                        grouped_messages = {}
                        for message in messages:
                            sender = message.get_sender_username()
                            if sender in grouped_messages:
                                grouped_messages[sender].append(message.get_message())
                            else:
                                grouped_messages[sender] = [message.get_message()]

                        # Iterate over the grouped messages and format them
                        for sender, messages in grouped_messages.items():
                            formatted_messages += f"> {sender}\n"
                            for message in messages:
                                formatted_messages += f"{message}\n"

                        # Remove the trailing newline character
                        formatted_messages = formatted_messages[:-1]

                        print('\n' + formatted_messages + '\n')
                    else:
                        print('\n' + response.get_error() + '\n')
                case Opcode.DELETE_ACCOUNT:
                    response = request(opcode=Opcode.DELETE_ACCOUNT,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':
                        print('\nYour account was deleted!\n')
                        break
                    else:
                        print('\n' + response.get_error() + '\n')

    except Exception as err:
        handler(err=err, **kwargs)
