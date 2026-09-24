import random

from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task


def random_otp():
  return random.randint(1000,9999)

@shared_task
def send_wellcome_email(email):
    subject = 'Welcome to Our Website'
    message = f'''
    <h1>Welcome to Our Website</h1>
    <p>Thank you for registering with us</p>
    <p>Your account has been created successfully</p>
    <p>Thank you</p>
    '''
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    fail_silently=False
    send_mail(subject, message, email_from, recipient_list,fail_silently=fail_silently)
    
@shared_task
def send_otp_email(email, otp):
    subject = 'Your OTP for Verification'
    message = f'''
    <h1>Your OTP for Verification</h1>
    <p>Your OTP is: {otp}</p>
    <p>This OTP will expire in 10 minutes</p>
    <p>Thank you</p>
    '''
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    fail_silently=False
    send_mail(subject, message, email_from, recipient_list,fail_silently=fail_silently)

    
@shared_task
def Partner_Join_With_Us(email,partner_id):
    subject = 'COngratulation You For Partner_id'
    message = f'''
    <h1>Auto Genrated Partner Id</h1>
    <p>Your Partner id Is : {partner_id}</p>
    <p>Dont Share This Id With Anyone</p>
    <p>Thank you</p>
    '''
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    fail_silently=False
    send_mail(subject, message, email_from, recipient_list,fail_silently=fail_silently)
   
