
import re
import hashlib
import hmac
import random
import string
from string import letters
import logging
import json

from datetime import datetime, timedelta
import datetime

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import app_identity

import cloudstorage as gcs

#stripe
import stripe

#for mandrill api
from google.appengine.api import urlfetch

import model
import emails

secret = 'pUbHuB123@!'
sender_email = "support@pubhub.co.za"
mandrill_key = "xAXcvG0ltJOK5o2-c7kilw"# Greenhouse mandrill api key pubhubza@gmail.com, greenhouse8903
#stripe_api_key = "sk_test_SH5MigqAy5iGL0oBbAwAWk4x"



# =================
# Pubhub Stripe API Keys
# =================
# test keys
# secret: sk_test_tjY7uCOmjf21UPZ1EbylApUo
# publishable: pk_test_hvec2hZOtSHy73M6V3GKnWGa

# live keys
# secret: sk_live_o387X0d7PzU6ZxoZr0gRW3EX     
# publishable: pk_live_zUMltZeOTPj0UgXI810qkw8X

stripe_api_key = "sk_live_o387X0d7PzU6ZxoZr0gRW3EX"
stripe_publishable_key = "pk_live_zUMltZeOTPj0UgXI810qkw8X"



app_id = app_identity.get_application_id()

#PW HASHING
def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)
    
def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))
    
# returns a cookie with a value value|hashedvalue
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())
# returns the origional value and validates if given hashed cookie matches our hash of the value    
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val
        
def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


#REGEX for register validtion
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return email and EMAIL_RE.match(email)
    
def request_blob_url(self, callback_url, max_bytes):
    upload_url = blobstore.create_upload_url(callback_url, max_bytes)
    return upload_url
    
def send_gmail(email, subject, body):
    try:
        logging.error("sending subscription mail")
        message = mail.EmailMessage(sender="Hollow Fish <%s>" % sender_email,
                                subject=subject)
        message.to = email
        message.html = body
        message.send()
    except:
        logging.error("couldnt send gmail... probably invalid email")

# ================================
# User handling
# ================================

def confirm_password(user, password):
    return valid_pw(user.email, password, user.pw_hash)

def check_postal_code(user_obj, postal_code):
    area = area_suburb_from_code(postal_code)[0]
    suburb = area_suburb_from_code(postal_code)[1]
    province = province_from_code(postal_code)

    user_obj.province = province
    user_obj.area = area
    user_obj.suburb = suburb
    user_obj.put()

def check_email(user_obj, email):
    existing_user = model.User.query(model.User.email == email).get()

    if existing_user:
        if existing_user.key.id() == user_obj.key.id():
            return True
        else:
            return False
    else:
        return True




# ================================
# Email Handling
# ================================

def send_email():
    logging.error("need to send some kind of email here.......")

# def send_mandrill_mail(subject, html, text, to_email):
def send_mandrill_mail(email_type, to_email):

    subject = emails.emails[email_type]["subject"]
    html = emails.emails[email_type]["html"]
    text = emails.emails[email_type]["text"]
    
    url = "https://mandrillapp.com/api/1.0/messages/send.json"

    form_json = {
            "key": mandrill_key,
            "message": {
                "html": html,
                "text": text,
                "subject": subject,
                "from_email": sender_email,
                "from_name": "PubHub",
                # "to": email_list,
                "to": [{
                    "email": to_email,
                    "name": "",
                    "type": "to"
                }],
                "headers": {
                    "Reply-To": sender_email
                },
                "important": False,
                "track_opens": True,
                "track_clicks": True,
                "auto_text": None,
                "auto_html": None,
                "inline_css": None,
                "url_strip_qs": None,
                "preserve_recipients": False,
                "view_content_link": None,
                "bcc_address": None,
                "tracking_domain": None,
                "signing_domain": None,
            },
            "async": False,
            "ip_pool": "Main Pool",
            "send_at": None
        }
    

    result = urlfetch.fetch(url=url, payload=json.dumps(form_json), method=urlfetch.POST)

    logging.error("MANDRILL RESULT")
    logging.error(dir(result))
    logging.error(result.status_code)
    logging.error(json.loads(result.content))

def send_mandrill_mail_template(email_obj, to_email):

    subject = email_obj["subject"]
    html = email_obj["html"]
    text = email_obj["text"]
    
    url = "https://mandrillapp.com/api/1.0/messages/send.json"

    form_json = {
            "key": mandrill_key,
            "message": {
                "html": html,
                "text": text,
                "subject": subject,
                "from_email": sender_email,
                "from_name": "PubHub",
                # "to": email_list,
                "to": [{
                    "email": to_email,
                    "name": "",
                    "type": "to"
                }],
                "headers": {
                    "Reply-To": sender_email
                },
                "important": False,
                "track_opens": True,
                "track_clicks": True,
                "auto_text": None,
                "auto_html": None,
                "inline_css": None,
                "url_strip_qs": None,
                "preserve_recipients": False,
                "view_content_link": None,
                "bcc_address": None,
                "tracking_domain": None,
                "signing_domain": None,
            },
            "async": False,
            "ip_pool": "Main Pool",
            "send_at": None
        }
    

    result = urlfetch.fetch(url=url, payload=json.dumps(form_json), method=urlfetch.POST)

    logging.error("MANDRILL RESULT")
    logging.error(dir(result))
    logging.error(result.status_code)
    logging.error(json.loads(result.content))


# ================================
# Postal Code Province matching
# ================================

def area_suburb_from_code(postal_code):
    # logging.error("hello utils..............area_suburb_from_code --> %s" % str(postal_code))

    if len( str(postal_code) ) < 4:
        postal_code = str(postal_code).zfill(4)

    postal_code_obj = model.PostalCode.query(model.PostalCode.postal_code == str(postal_code)).get()
    # logging.error(postal_code_obj)
    if postal_code_obj:
        return [ postal_code_obj.area, postal_code_obj.suburb ]
    else:
        logging.error(" - - - - -  - - - - no postal code found.......")
        return [None, None]

def province_from_code(postal_code):
    logging.error("PROVINCE FROM CODE . . . . . . . . . ")
    try:
        postal_code = int(postal_code)
        logging.error("PROVINCE FROM CODE, again . . . . . . . . . ")

        # if 0 <= postal_code > 300:
        #     return "Gauteng"
        # elif 300 <= postal_code < 500:
        #     return "North West"
        # elif 300 <= postal_code < 500

        #     "Limpopo"
        #     "Mpumalanga"
        #     "KwaZulu-Natal"
        #     "Eastern Cape"
        #     "Western Cape"
        #     "Northern Cape"
        #     "Free State"

        gauteng = [(1,299), (1400,2199)]
        north_west = [(300,499), (2500,2899)]
        limpopo = [(500,999)]
        mpumalanga = [(1000,1399), (2200, 2499)]
        kwazulu_natal = [(2900,4730)]
        eastern_cape = [(4731,6499)]
        western_cape = [(6500,8099)]
        northern_cape = [(8100,8999)]
        free_state = [(9300,9999)]

        if any(lower <= postal_code <= upper for (lower, upper) in gauteng):
            return "Gauteng"
        elif any(lower <= postal_code <= upper for (lower, upper) in north_west):
            return "North West"
        elif any(lower <= postal_code <= upper for (lower, upper) in limpopo):
            return "Limpopo"
        elif any(lower <= postal_code <= upper for (lower, upper) in mpumalanga):
            return "Mpumalanga"
        elif any(lower <= postal_code <= upper for (lower, upper) in kwazulu_natal):
            return "KwaZulu-Natal"
        elif any(lower <= postal_code <= upper for (lower, upper) in eastern_cape):
            return "Eastern Cape"
        elif any(lower <= postal_code <= upper for (lower, upper) in western_cape):
            return "Western Cape"
        elif any(lower <= postal_code <= upper for (lower, upper) in northern_cape):
            return "Northern Cape"
        elif any(lower <= postal_code <= upper for (lower, upper) in free_state):
            return "Free State"
    except:
        return ""

        # ranges = [(1000,2429), (2545,2575), (2640,2686), (2890, 2890)]
        # if any(lower <= postcode <= upper for (lower, upper) in ranges):
        #     print('M')




# ================================
# Counter
# ================================

def update_counter(count_type):

    counter = model.Count.query().get()
    if not counter:
        counter = model.Count(employees=0)
        counter.put()

    if count_type == "employees":
        counter.employees += 1
    if count_type == "clients":
        counter.clients += 1
    if count_type == "registrations":
        counter.registrations += 1
    if count_type == "referrals":
        counter.referrals += 1
    if count_type == "cancellations":
        counter.cancellations += 1
    counter.put()

def decrement_counter(count_type):

    counter = model.Count.query().get()
    if not counter:
        counter = model.Count(employees=0)
        counter.put()

    if count_type == "employees":
        counter.employees -= 1
    if count_type == "clients":
        counter.clients -= 1
    if count_type == "registrations":
        counter.registrations -= 1
    if count_type == "referrals":
        counter.referrals -= 1
    if count_type == "cancellations":
        counter.cancellations -= 1
    counter.put()

# ================================
# Payments
# ================================

def create_stripe_subscription_plan():
    stripe.api_key = "sk_test_SH5MigqAy5iGL0oBbAwAWk4x"
    stripe.Plan.create(
      amount=30000,
      interval='month',
      name='TGH Recruitment Plan',
      currency='zar',
      id='tghr_basic')

    existing_plan = model.SubscriptionPlan.query().get()

    if not existing_plan:
        existing_plan = model.SubscriptionPlan().put()

def unsubscribe_user(user):
    stripe.api_key = stripe_api_key

    if user.stripeCustomer:
        stripe_customer_id = json.loads(json.dumps(user.stripeCustomer))["id"]
        customer = stripe.Customer.retrieve(stripe_customer_id)

        logging.error("......................deleting subscription for customer. . . . ")
        # logging.error(customer)

        subscription_id = json.loads(json.dumps(user.stripeCustomer))['subscriptions']['data'][0]['id']

        subscription = customer.subscriptions.retrieve(subscription_id)
        logging.error(subscription)
        period_end = subscription.current_period_end


        customer.subscriptions.retrieve(subscription_id).delete(at_period_end=True)

        # don't mark user as paid: false until period end
        #user.paid = False
        #user.paying = False
        #user.put()

        update_counter("cancellations")


        user.period_end = datetime.datetime.fromtimestamp(int(period_end))
        user.date_cancelled = datetime.datetime.now()
        # testing
        # user.period_end = datetime.datetime.now() + datetime.timedelta(0,300)
        user.put()
        # SEND NOTIFICATION EMAIL
        # send_mandrill_mail("cancelled_subscription", user.email)
        name = ""
        if user.name:
            name = user.name
        emails.render_and_send_email_template("cancelled_subscription", user.email, name=name)

        return datetime.datetime.fromtimestamp(int(period_end))
    else:
        return False

# ================================
# Using this to create a new temporary password
# ================================
def generate_random_token(N):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(N))




#saving blobkey to seller obj along with serving url
def save_blob_to_image_obj(blob_key, price, title, description):
    img_url = images.get_serving_url(blob_key)
    portfolio_image = model.Images(img_url=img_url, img_key=blob_key, price=price, title=title, description=description)
    portfolio_image.put()
    return img_url

def save_gcs_to_media(gcs_filename, serving_url):
    media = model.Media(gcs_filename=gcs_filename, serving_url=serving_url)
    media.put()
    return media.key

def delete_media(gcs_filename):
    images.delete_serving_url(blobstore.create_gs_key(gcs_filename))
    gcs.delete(gcs_filename[3:])
    return True
    
    
    
    
    
    
    
    
    
    