import jinja2
import logging
import os
import utils

template_dir = os.path.join(os.path.dirname(__file__), 'templates/emails')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

# emails = {
    
#     "registration": {
#         "subject": "Thanks for registering with PubHub",
#         "html": "Thanks for registering with PubHub, you can login to your profile page online <a href='http://pubhub.co.za/login'>here</a> and adjust your basic settings, subscribe or unsubscribe etc.",
#         "text": "Thanks for registering with PubHub, you can login to your profile page online at http://pubhub.co.za/login and adjust your basic settings, subscribe, unsubscribe etc."
#     },
#     "subscribed": {
#         "subject": "Thanks for subscribing to PubHub",
#         "html": "Thanks for subscribing to PubHub, you can login to your profile page online <a href='http://pubhub.co.za/login'>here</a> and adjust your basic settings.<br> We hope you enjoy our service.",
#         "text": "Thanks for subscribing to PubHub, you can login to your profile page online at http://pubhub.co.za/login and adjust your basic settings. We hope you enjoy our service."
#     },
#     "successful_payment": {
#         "subject": "PubHub - Payment received",
#         "html": "Thanks for your payment, if you have any concerns or questions please contact us at <a href='mailto:support@pubhub.co.za'>support@pubhub.co.za<a/>",
#         "text": "Thanks for your payment, if you have any concerns or questions please contact us at support@pubhub.co.za"
#     },
#     "failed_payment": {
#         "subject": "PubHub - Payment failed",
#         "html": "It looks like there was a problem with your payment, it might be that your credit card is no longer valid or was recently cancelled, you can update your card details <a href='http://pubhub.co.za/user/profile'>here</a>",
#         "text": "It looks like there was a problem with your payment, it might be that your credit card is no longer valid or was recently cancelled, you can update your card details at http://pubhub.co.za/user/profile"
#     },
#     "cancelled_subscription": {
#         "subject": "PubHub - Subscription Cancelled",
#         "html": "We're sorry to see you go, your subscription to PubHub has been cancelled, you can still login at anytime and <a href='http://pubhub.co.za/user/profile'>rejoin the service</a>, thank you for your support.",
#         "text": "We're sorry to see you go, your subscription to PubHub has been cancelled, you can still login at anytime and rejoin the service at http://pubhub.co.za/user/profile, thank you for your support."
#     },
#     "forgot_password": {
#         "subject": "PubHub - Forgotten Password",
#         "html": "",
#         "text": "We're sorry to see you go, your subscription to PubHub has been cancelled, you can still login at anytime and rejoin the service at http://pubhub.co.za/user/profile, thank you for your support."
#     }

# }

def get_email_template(template, string_tuple_subject, string_tuple_html, string_tuple_text):
    emails = {
        "registration": {
            "subject": "Thanks for registering with PubHub",
            "html": "Thanks for registering with PubHub, you can login to your profile page online <a href='http://pubhub.co.za/login'>here</a> and adjust your basic settings, subscribe or unsubscribe etc.",
            "text": "Thanks for registering with PubHub, you can login to your profile page online at http://pubhub.co.za/login and adjust your basic settings, subscribe, unsubscribe etc."
        },
        "subscribed": {
            "subject": "Thanks for subscribing to PubHub",
            "html": "Thanks for subscribing to PubHub, you can login to your profile page online <a href='http://pubhub.co.za/login'>here</a> and adjust your basic settings.<br> We hope you enjoy our service.",
            "text": "Thanks for subscribing to PubHub, you can login to your profile page online at http://pubhub.co.za/login and adjust your basic settings. We hope you enjoy our service."
        },
        "successful_payment": {
            "subject": "PubHub - Payment received",
            "html": "Thanks for your payment, if you have any concerns or questions please contact us at <a href='mailto:support@pubhub.co.za'>support@pubhub.co.za<a/>",
            "text": "Thanks for your payment, if you have any concerns or questions please contact us at support@pubhub.co.za"
        },
        "failed_payment": {
            "subject": "PubHub - Payment failed",
            "html": "It looks like there was a problem with your payment, it might be that your credit card is no longer valid or was recently cancelled, you can update your card details <a href='http://pubhub.co.za/user/profile'>here</a>",
            "text": "It looks like there was a problem with your payment, it might be that your credit card is no longer valid or was recently cancelled, you can update your card details at http://pubhub.co.za/user/profile"
        },
        "cancelled_subscription": {
            "subject": "PubHub - Subscription Cancelled",
            "html": "We're sorry to see you go, your subscription to PubHub has been cancelled, you can still login at anytime and <a href='http://pubhub.co.za/user/profile'>rejoin the service</a>, thank you for your support.",
            "text": "We're sorry to see you go, your subscription to PubHub has been cancelled, you can still login at anytime and rejoin the service at http://pubhub.co.za/user/profile, thank you for your support."
        },
        "forgot_password": {
            "subject": "PubHub - Forgotten Password",
            "html": "Hi<br> your new temporary password is %s, please make sure you change your password when you next log in.<br><br> Regards Pubhub Team",
            "text": "Hi<br> your new temporary password is %s, please make sure you change your password when you next log in.<br><br> Regards Pubhub Team"
        }
    }

    subject = emails[template]["subject"] % string_tuple_subject
    html = emails[template]["html"] % string_tuple_html
    text = emails[template]["text"] % string_tuple_text

    email_obj = {
        "subject": subject,
        "html": html,
        "text": text
    }

    return email_obj


def render_and_send_email_template(template_name, email, **params):
    logging.error("PARAMS")
    logging.error(params)
    try:
        new_pw = params["new_pw"]
        logging.error(params["new_pw"])
    except:
        new_pw = "please contact support.pubhub.co.za for your temporary password"

    emails = {
        "registration": {
            "subject": "Thanks for registering with PubHub",
            "template": "registration.html",
            "text": "Thank you for downloading PubHub and registering your details. Please note that your details will not be shared with any 3rd party.\r\nTo access the staff with the skills you need please sign up with a payment of R315.00 per month.\r\nPlease note that this is a monthly fee but can be stopped at any time by you\r\n\r\n Pubhub Team"
        },
        "subscribed": {
            "subject": "PubHub - Thanks for subscribing!",
            "template": "receipt.html",
            "text": "Thanks for subscribing to PubHub, you can login to your profile page online at http://pubhub.co.za/login and adjust your basic settings. We hope you enjoy our service."
        },
        "successful_payment": {
            "subject": "PubHub - Payment received",
            "template": "receipt.html",
            "text": "Thank you, we have received your payment.\r\n Your monthly payment of R315.00 will allow you unlimited access to all the staff you need for the period of a month.\r\n Your access and payments can be cancelled at any time by you. Simply email support@pubhub.co.za.\r\n\r\n Pubhub Team"
        },
        "failed_payment": {
            "subject": "PubHub - Payment failed",
            "template": "failed_payment.html",
            "text": "Hi \r\n It looks like there was a problem with your payment, it might be that your credit card is no longer valid or was recently cancelled, you can update your card details at http://pubhub.co.za/user/profile\r\n\r\n Pubhub Team"
        },
        "cancelled_subscription": {
            "subject": "PubHub - Subscription Cancelled",
            "template": "cancelled_subscription.html",
            "text": "Hi,\r\n We're sorry to see you go, your subscription to PubHub has been cancelled, you can still login at anytime and rejoin the service at http://pubhub.co.za/user/profile, thank you for your support.\r\n\r\n Pubhub Team"
        },
        "forgot_password": {
            "subject": "PubHub - Forgotten Password",
            "template": "forgot_password.html",
            "text": "Hi,\r\n We have received a request to have your password reset for PubHub. If you did not request this then please ignore this email.\r\n To reset your password please log in with the below and then choose a new password from your settings:\r\n %s,\r\n\r\n Pubhub Team" % new_pw
        }
    }

    template = emails[template_name]["template"]

    t = jinja_env.get_template(template)
    html = t.render(params)

    email_obj = {
        "html": html,
        "text": emails[template_name]["text"],
        "subject": emails[template_name]["subject"]
    }

    utils.send_mandrill_mail_template(email_obj, email)

    return html