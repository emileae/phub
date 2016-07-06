from google.appengine.ext import ndb

import utils

# def users_key(group='default'):
#     return ndb.Key('users', group)
    
class User(ndb.Model):
    name = ndb.StringProperty()
    fname = ndb.StringProperty()
    lname = ndb.StringProperty()
    postal_code = ndb.StringProperty()
    province = ndb.StringProperty()
    # city = ndb.KeyProperty(kind="City")
    # suburb = ndb.KeyProperty(kind="Suburb")
    # region = ndb.KeyProperty(kind="Region")
    # location = ndb.KeyProperty(kind="Location")
    email = ndb.StringProperty()
    pw_hash = ndb.StringProperty()
    paying = ndb.BooleanProperty(default=False)
    paid = ndb.BooleanProperty(default=False)
    date_paid = ndb.DateTimeProperty()
    date_cancelled = ndb.DateTimeProperty(default=None)
    stripeToken = ndb.StringProperty()
    stripeCustomerID = ndb.StringProperty()
    stripeCardID = ndb.StringProperty()
    stripeCustomer = ndb.JsonProperty()
    period_end = ndb.DateTimeProperty(default=None)
    approved = ndb.BooleanProperty(default=True)
    
    @classmethod
    def by_id(cls, uid):
        # return cls.get_by_id(uid, parent = users_key())
        return cls.get_by_id(uid)
    
    @classmethod
    def login(cls, email, pw):
        u = cls.by_email(email)
        if u and utils.valid_pw(email, pw, u.pw_hash):
            return u
            
    @classmethod
    def by_email(cls, email):
        u = User.query(User.email == email).get()
        return u

# =============================
# Recruitment models
# =============================

# =============================
# Stripe Events
# =============================

class StripeEvent(ndb.Model):
    event = ndb.JsonProperty()
    event_type = ndb.StringProperty()
    customer_id = ndb.StringProperty()
    userID = ndb.StringProperty(default="")
    created = ndb.DateTimeProperty(auto_now_add=True)


class Count(ndb.Model):
    employees = ndb.IntegerProperty(default=0)
    clients = ndb.IntegerProperty(default=0)
    cancellations = ndb.IntegerProperty(default=0)
    registrations = ndb.IntegerProperty(default=0)
    referrals = ndb.IntegerProperty(default=0)
    created = ndb.DateTimeProperty(auto_now_add=True)

class SubscriptionPlan(ndb.Model):
    amount=ndb.IntegerProperty(default=31500)
    interval=ndb.StringProperty(default='month')
    name=ndb.StringProperty(default='TGH Recruitment Plan')
    currency=ndb.StringProperty(default='zar')
    id=ndb.StringProperty(default='tghr_basic')

# remove  tim@the-greenhouse.co.za and tiM@the-greenhouse.com emaile.app@gmail emile.esterhuizen@gmail

class CapturedEmployee(ndb.Model):
    name = ndb.StringProperty()
    gender = ndb.StringProperty()
    
    postal_code_id = ndb.StringProperty()
    postal_code = ndb.IntegerProperty()
    province = ndb.StringProperty()
    area = ndb.StringProperty(default=None)
    suburb = ndb.StringProperty(default=None)

    total_skills = ndb.IntegerProperty(default=0)
    
    # city = ndb.StringProperty()
    # suburb = ndb.StringProperty()
    # near_cbd = ndb.BooleanProperty()
    # can_commute = ndb.BooleanProperty()
    
    # bartender = ndb.BooleanProperty()
    # manager = ndb.BooleanProperty()
    # waiter = ndb.BooleanProperty()
    # kitchen = ndb.BooleanProperty()
    # received_training = ndb.BooleanProperty()
    bartender = ndb.StringProperty()
    manager = ndb.StringProperty()
    waiter = ndb.StringProperty()
    kitchen = ndb.StringProperty()
    received_training = ndb.StringProperty()

    phone = ndb.StringProperty()

    # canwork = ndb.BooleanProperty()
    canwork = ndb.StringProperty(default="yes")

    reference_name = ndb.StringProperty()
    reference_duration = ndb.StringProperty()
    reference_contact = ndb.StringProperty()

    coffee = ndb.BooleanProperty()
    wine = ndb.BooleanProperty()
    front_manage = ndb.BooleanProperty()
    cocktail = ndb.BooleanProperty()
    silver = ndb.BooleanProperty()
    scullery = ndb.BooleanProperty()
    cook = ndb.BooleanProperty()
    back_manage = ndb.BooleanProperty()
    food_manage = ndb.BooleanProperty()

    email = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)

class Location(ndb.Model):
    city = ndb.StringProperty()
    suburb = ndb.StringProperty()
    province = ndb.StringProperty()

class Employee(ndb.Model):
    name = ndb.StringProperty()
    email_contact = ndb.StringProperty()
    phone_contact = ndb.StringProperty()
    position = ndb.StringProperty()
    suburb = ndb.StringProperty()
    city = ndb.StringProperty()
    region = ndb.StringProperty()
    active = ndb.BooleanProperty(default=True)
    skills = ndb.StringProperty(repeated=True)

    bartender = ndb.BooleanProperty()
    manager = ndb.BooleanProperty()
    waitress = ndb.BooleanProperty()
    host = ndb.BooleanProperty()
    draught = ndb.BooleanProperty()
    cocktail = ndb.BooleanProperty()
    wine = ndb.BooleanProperty()
    spirits = ndb.BooleanProperty()
    coffee = ndb.BooleanProperty()


class PostalCode(ndb.Model):
    area = ndb.StringProperty()
    suburb = ndb.StringProperty()
    postal_code = ndb.StringProperty()
    box_postal_code = ndb.StringProperty()
    street_postal_code = ndb.StringProperty()

class City(ndb.Model):
    city = ndb.StringProperty()

class Suburb(ndb.Model):
    suburb = ndb.StringProperty()

class Region(ndb.Model):
    region = ndb.StringProperty()




class Media(ndb.Model):
    gcs_filename = ndb.StringProperty(default = None)
    serving_url = ndb.StringProperty(default = None)
    created = ndb.DateTimeProperty(auto_now_add=True)
    
class Contact(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    description = ndb.TextProperty()
    web = ndb.BooleanProperty(default=False)
    mobile = ndb.BooleanProperty(default=False)
    game = ndb.BooleanProperty(default=False)
    spam = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)

class Subscriber(ndb.Model):
    email = ndb.StringProperty()
    name = ndb.StringProperty()
    active = ndb.BooleanProperty(default=True)
    created = ndb.DateTimeProperty(auto_now_add=True)



# ============================================
# Payments
# ============================================

class PayfastPayment(ndb.Model):
    m_payment_id = ndb.StringProperty()
    pf_payment_id = ndb.StringProperty()
    payment_status = ndb.StringProperty()
    item_name = ndb.StringProperty()
    item_description = ndb.StringProperty()
    amount_gross = ndb.StringProperty()
    amount_fee = ndb.StringProperty()
    amount_net = ndb.StringProperty()
    custom_int1 = ndb.StringProperty()# can be up to 5 custom_int1-5
    custom_str1 = ndb.StringProperty()# can be up to 5 custom_str1-5
    name_first = ndb.StringProperty()
    name_last = ndb.StringProperty()
    email_address = ndb.StringProperty()
    merchant_id = ndb.StringProperty()
    signature = ndb.StringProperty()

    user = ndb.KeyProperty(kind='User')

    created = ndb.DateTimeProperty(auto_now_add=True)

class TokenCount(ndb.Model):
    count = ndb.IntegerProperty(default=0)
    created = ndb.DateTimeProperty(auto_now_add=True)

class UsedToken(ndb.Model):
    token = ndb.StringProperty()
    payment = ndb.KeyProperty(kind="PayfastPayment")
    purchased = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)




    
    
    

    