from django.shortcuts import render
import imapclient
import email
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from .models import Email
from django.http import HttpResponseServerError
def decrypt_message(encrypted_message, private_key_path, private_key_password):
    if not encrypted_message:
        return ""

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=private_key_password.encode(),
            backend=default_backend()
        )

    decrypted_message = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_message.decode()

def fetch_emails():
    # Connect to the IMAP server
    server = imapclient.IMAPClient('imap.gmail.com', ssl=True)
    server.login('syash5824@gmail.com', 'qeog rnfa rihe vdrw')

    # Select the mailbox and fetch the most recent emails
    server.select_folder('INBOX')
    emails = server.search(['ALL'])

    # Get the last 5 email IDs
    last_5_emails = sorted(emails, reverse=True)[:5]

    # Retrieve the stored emails from the database based on the last 5 email IDs
    stored_emails = Email.objects.filter(uid__in=last_5_emails).order_by('-received_date')

    # Store the fetched emails in the database if they don't already exist
    for uid in last_5_emails:
        if not stored_emails.filter(uid=uid).exists():
            response = server.fetch(uid, ['RFC822', 'INTERNALDATE'])
            message_data = response[uid][b'RFC822']
            email_message = email.message_from_bytes(message_data)

            email_obj = Email()
            email_obj.uid = uid
            email_obj.subject = email_message.get('Subject', '')
            email_obj.sender = email_message.get('From', '')
            email_obj.received_date = response[uid][b'INTERNALDATE'].strftime('%Y-%m-%d %H:%M:%S')

            # Decrypt the email body if it is encrypted
            if email_message.get('Content-Transfer-Encoding', '').upper() == 'BASE64':
                encrypted_body = email_message.get_payload()
                decrypted_body = decrypt_message(encrypted_body, 'path/to/private_key.pem', 'private_key_password')
                email_obj.body = decrypted_body
            else:
                email_obj.body = email_message.get_payload()

            email_obj.save()

def email_list(request):
    try:
        # Fetch the emails manually on page load
        fetch_emails()

        # Retrieve the latest 5 stored emails from the database
        emails = Email.objects.order_by('-received_date')[:5]

        return render(request, 'emailapp/email_list.html', {'emails': emails})

    except Exception as e:
        # Ignore the Broken pipe error and return a generic error response
        if isinstance(e, BrokenPipeError):
            return HttpResponseServerError("An error occurred")
        else:
            raise e
