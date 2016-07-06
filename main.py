#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import logging
import os
from string import letters
import json
from datetime import datetime, timedelta
import datetime
import time
import urllib
import csv

# for candidate queries sorting by name
from operator import itemgetter

#stripe
import stripe

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.datastore.datastore_query import Cursor

from google.appengine.api import taskqueue

import model
import utils
import emails

import cloudstorage as gcs

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

cookie_name = "za.co.thegreenhouse.recruitment"
# stripe_api_key = "sk_test_SH5MigqAy5iGL0oBbAwAWk4x"

def space_capitalize(value):
    value_array = value.split(" ")
    capital_array = []
    for v in value_array:
        capital_array.append(v.capitalize())
    return " ".join(capital_array)
jinja_env.filters['space_capitalize'] = space_capitalize


def check_bool_checkbox(value):
    if not value or len(value) <= 0:
        value = ""
    else:
        return "checked"
jinja_env.filters['check_bool_checkbox'] = check_bool_checkbox

def check_none(value):
    if not value:
        value = ""
    return value
jinja_env.filters['check_none'] = check_none

def blog_date(value):
    return value.strftime("%d/%m/%y")
jinja_env.filters['blog_date'] = blog_date

class MainHandler(webapp2.RequestHandler):

#TEMPLATE FUNCTIONS    
    def write(self, *a, **kw):
        self.response.headers['Host'] = 'localhost'
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        params['user'] = self.user
        #params['buyer'] = self.buyer
        t = jinja_env.get_template(template)
        return t.render(params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    #JSON rendering
    def render_json(self, obj):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.headers['Host'] = 'localhost'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.out.write(json.dumps(obj))
   
    #COOKIE FUNCTIONS
    # sets a cookie in the header with name, val , Set-Cookie and the Path---not blog    
    def set_secure_cookie(self, name, val):
        cookie_val = utils.make_secure_val(val)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))# consider imcluding an expire time in cookie(now it closes with browser), see docs
    # reads the cookie from the request and then checks to see if its true/secure(fits our hmac)    
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        if cookie_val:
            cookie_val = urllib.unquote(cookie_val)
        return cookie_val and utils.check_secure_val(cookie_val)
    
    def login(self, user):
        self.set_secure_cookie(cookie_name, str(user.key.id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', '%s=; Path=/' % cookie_name)
    
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie(cookie_name)

        self.user = uid and model.User.by_id(int(uid))
        
class Register(MainHandler):
    def get(self):
        user_obj = self.user
        if user_obj:
            self.redirect("/")
        else:
            self.render("register.html")
    def post(self):
        name = self.request.get('name')
        email = self.request.get('email')
        password = self.request.get('password')
        verify_password = self.request.get('verify_password')
        key = self.request.get('key')
        
        error = False
        error_name = ""
        error_password = ""
        error_email = ""
        error_verify = ""
        
        if not utils.valid_username(name):
            error_name="Your username needs to be between 3 and 20 characters long and only contain numbers and letters"
            error = True
            
        if not utils.valid_password(password):
            error_password="Your password needs to be between 3 and 20 characters long"
            error = True
            
        if not utils.valid_email(email):
            error_email="Please type in a valid email address"
            error = True
            
        if password != verify_password:
            error_verify="Please ensure your passwords match"
            error = True
            
        if key != "Nicholas001":
            error_key="Please provide the correct key"
            error = True
        
        if not error:
            pw_hash = utils.make_pw_hash(name, password)
            user = model.User(parent=model.users_key(), name=name, email=email, pw_hash=pw_hash)
            user.put()
            self.login(user)
            self.redirect('/fileupload')
            
        else:
            js_code = "$('#register').modal('show');"
            data = {
                'error_name':error_name,
                'error_password':error_password,
                'error_email':error_email,
                'error_verify':error_verify,
                'error_key':error_key,
                'js_code':js_code
            }

            self.render('register.html', data=data)
            
            """
            In order to manually show the modal pop up you have to do this

            $('#myModal').modal('show');
            You previously need to initialize it with show: false so it won't show until you manually do it.

            $('#myModal').modal({ show: false})
            """
class LoginRegister(MainHandler):
    def get(self):
        data = None
        self.render("login.html", data=data)
        
class Login(MainHandler):
    def get(self):
        error = self.request.get("error")

        error_msg = False
        if error:
            error_msg = "invalid username / password, have you registered?"

        self.render("login.html", error_msg=error_msg)
    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')

        s = model.User.login(email, password)
        if s:
            self.login(s)
            self.redirect('/user/profile')
        else:
            self.redirect('/login?error=true')
        
class Logout(MainHandler):
    def get(self):
        self.logout()
        self.redirect('/')        
        
# =========================
# Public pages
# =========================

class Home(MainHandler):
    def get(self):
        year = datetime.datetime.now().year
        self.render('index.html', year=year)
        
# =========================
# Admin pages
# =========================

class Admin(MainHandler):
    def get(self):

        counter = model.Count.query().get()

        self.render('cms.html', counter=counter)

class AdminLocations(MainHandler):
    def get(self):

        location_id = self.request.get("location_id")

        location = False
        if location_id:
            location = model.Location.get_by_id(int(location_id))

        locations = model.Location.query().fetch()
        self.render("admin-location.html", locations=locations, location=location)

    def post(self):
        city = self.request.get("city")
        suburb = self.request.get("suburb")
        province = self.request.get("province")

        delete = self.request.get("delete")

        if delete:
            location = model.Location.get_by_id(int(delete))
            location.key.delete()
        else:
            city = city.lower()
            suburb = suburb.lower()
            province = province.lower()

            location = model.Location(city=city, suburb=suburb, province=province)
            location.put()

        self.redirect("/admin/locations")

class AdminClients(MainHandler):
    def get(self):

        client_email = self.request.get("email")

        curs = Cursor(urlsafe=self.request.get('cursor'))
        if client_email:
            clients, next_curs, more = model.User.query(model.User.email == client_email).order(-model.User.name).fetch_page(50, start_cursor=curs)
        else:
            clients, next_curs, more = model.User.query().order(-model.User.name).fetch_page(50, start_cursor=curs)
        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False

        self.render("admin-clients.html", clients=clients, next_curs=next_curs)

class AdminClient(MainHandler):
    def get(self, client_id):
        client = model.User.get_by_id(int(client_id))
        self.render("admin-client.html", client=client)

class AdminEmployees(MainHandler):
    def get(self):
        page = self.request.get("page")
        if not page:
            page = 1
        else:
            page = int(page) + 1

        curs = Cursor(urlsafe=self.request.get('cursor'))

        employee_email = self.request.get("email")

        if employee_email:
            employees, next_curs, more = model.CapturedEmployee.query(model.CapturedEmployee.email == employee_email).order(-model.CapturedEmployee.created).fetch_page(300, start_cursor=curs)
        else:
            employees, next_curs, more = model.CapturedEmployee.query().order(-model.CapturedEmployee.created).fetch_page(300, start_cursor=curs)
        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False

        self.render("admin-employees.html", employees=employees, next_curs=next_curs, page=page)

class AdminEmployeesCSV(MainHandler):
    def get(self):
        page = self.request.get("page")
        if not page:
            page = 1
        curs = Cursor(urlsafe=self.request.get('cursor'))
        employees, next_curs, more = model.CapturedEmployee.query().order(-model.CapturedEmployee.created).fetch_page(300, start_cursor=curs)
        
        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False

        self.response.headers['Content-Type'] = 'text/csv'
        self.response.headers['Content-Disposition'] = 'attachment; filename=pubhub_candidate_emails_%s.csv' % str(page)
        writer = csv.writer(self.response.out)

        writer.writerow([
            'Page %s' % page, 
            ])

        writer.writerow([
            'Name', 
            'Email',
            'Phone',
            'Postal Code'
            ])
        for e in employees:
            # self.writer.writerow([unicode(s).encode("utf-8") for s in row])
            name = unicode(e.name).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', r.name)
            email = unicode(e.email).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', r.email)
            phone = unicode(e.phone).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', r.email)
            postal_code = unicode(e.postal_code).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', r.email)
            writer.writerow([
                name,
                email,
                phone,
                postal_code
                ])

class AdminEmployee(MainHandler):
    def get(self, employee_id):
        employee = model.CapturedEmployee.get_by_id(int(employee_id))

        cities = model.City.query().order(model.City.city).fetch()
        suburbs = model.Suburb.query().order(model.Suburb.suburb).fetch()
        locations = model.Location.query().fetch()

        error_no_name = False
        error_no_location = False
        error_no_mobile = False
        error_no_email = False
        error_no_craft = False
        error_no_skill = False

        def stringifyBool(bool):
            if bool:
                return "yes"
            else:
                return ""

        postal_code = None
        if employee.postal_code_id:
            postal_code = model.PostalCode.get_by_id(int(employee.postal_code_id))

        logging.error("------------ postal code: %s" % ( postal_code.postal_code ))

        self.render("admin-employee.html", 
                name = employee.name,
                gender = employee.gender,
                # city = employee.city,

                postal_code_id = employee.postal_code_id,
                postal_code=postal_code,

                # can_commute = employee.can_commute,
                # suburb = employee.suburb,
                # bartender = stringifyBool( employee.bartender ),
                # manager = stringifyBool( employee.manager ),
                # waiter = stringifyBool( employee.waiter ),
                # kitchen = stringifyBool( employee.kitchen ),
                bartender = employee.bartender,
                manager = employee.manager,
                waiter = employee.waiter,
                kitchen = employee.kitchen,

                phone = employee.phone,
                
                # canwork = stringifyBool( employee.canwork ),
                canwork = employee.canwork,

                coffee = stringifyBool( employee.coffee ),
                wine = stringifyBool( employee.wine ),
                front_manage = stringifyBool( employee.front_manage ),
                cocktail = stringifyBool( employee.cocktail ),
                silver = stringifyBool( employee.silver ),
                scullery = stringifyBool( employee.scullery ),
                cook = stringifyBool( employee.cook ),
                back_manage = stringifyBool( employee.back_manage ),
                food_manage = stringifyBool( employee.food_manage ),
                email = employee.email,
                error_no_name=error_no_name,
                error_no_location=error_no_location,
                error_no_mobile=error_no_mobile,
                error_no_email=error_no_email,
                error_no_craft=error_no_craft,
                error_no_skill=error_no_skill,
                # cities=cities,
                # suburbs=suburbs,
                employee=employee
                # locations=locations
                )

    def post(self, employee_id):
        def boolify(value):
            if value and value == 'yes':
                value = True
            else:
                value = False
            return value

        def unboolify(value):
            if value:
                value = 'yes'
            else:
                value = 'no'
            return value

        name = self.request.get("name")
        gender = self.request.get("gender")
        city = self.request.get("city")
        can_commute = boolify( self.request.get("can_commute") )
        suburb = self.request.get("suburb")
        bartender = boolify( self.request.get("bartender") )
        manager = boolify( self.request.get("manager") )
        waiter = boolify( self.request.get("waiter") )
        kitchen = boolify( self.request.get("kitchen") )
        phone = self.request.get("phone")
        canwork = boolify( self.request.get("canwork") )
        coffee = boolify( self.request.get("coffee") )
        wine = boolify( self.request.get("wine") )
        front_manage = boolify( self.request.get("front_manage") )
        cocktail = boolify( self.request.get("cocktail") )
        silver = boolify( self.request.get("silver") )
        scullery = boolify( self.request.get("scullery") )
        cook = boolify( self.request.get("cook") )
        back_manage = boolify( self.request.get("back_manage") )
        food_manage = boolify( self.request.get("food_manage") )
        email = self.request.get("email")

        if employee_id:
            employee = model.CapturedEmployee.get_by_id(int(employee_id))

            error_no_name = False
            error_no_location = False
            error_no_mobile = False
            error_no_email = False
            error_no_craft = False
            error_no_skill = False

            error = False

            if name:
                error_no_name = False
            else:
                error_no_name = True

            if bartender or manager or waiter or kitchen:
                error_no_craft = False
            else:
                error_no_craft = True
                error = True

            if coffee or wine or front_manage or cocktail or silver or scullery or cook or back_manage or food_manage:
                error_no_skill = False
            else:
                error_no_skill = True
                error = True


            logging.error("city...%s" % city)
            if city or suburb:
                error_no_location = False
            else:
                error_no_location = True
                error = True

            if not phone:
                error_no_mobile = True
                error = True

            if not email or not utils.valid_email(email):
                error_no_email = True
                error = True

            if not error:
                ce = employee

                ce.name = name
                ce.gender = gender
                ce.city=city
                ce.can_commute=can_commute
                ce.suburb=suburb
                ce.bartender=bartender
                ce.manager=manager
                ce.waiter=waiter
                ce.kitchen=kitchen
                ce.phone=phone
                ce.canwork=canwork
                ce.coffee=coffee
                ce.wine=wine
                ce.front_manage=front_manage
                ce.cocktail=cocktail
                ce.silver=silver
                ce.scullery=scullery
                ce.cook=cook
                ce.back_manage=back_manage
                ce.food_manage=food_manage
                ce.email=email

                ce.put()

                self.redirect("/admin/employee/%s" % employee_id)

            else:
                def stringifyBool(bool):
                    if bool:
                        return "yes"
                    else:
                        return ""

                logging.error("Invalid Form gender: %s" % gender)

                cities = model.City.query().order(model.City.city).fetch()
                suburbs = model.Suburb.query().order(model.Suburb.suburb).fetch()

                locations = model.Location.query().fetch()

                self.render("admin-employee.html", 
                name = name,
                gender = gender,
                city = city,
                can_commute = can_commute,
                suburb = suburb,
                bartender = stringifyBool( bartender ),
                manager = stringifyBool( manager ),
                waiter = stringifyBool( waiter ),
                kitchen = stringifyBool( kitchen ),
                phone = phone,
                canwork = stringifyBool( canwork ),
                coffee = stringifyBool( coffee ),
                wine = stringifyBool( wine ),
                front_manage = stringifyBool( front_manage ),
                cocktail = stringifyBool( cocktail ),
                silver = stringifyBool( silver ),
                scullery = stringifyBool( scullery ),
                cook = stringifyBool( cook ),
                back_manage = stringifyBool( back_manage ),
                food_manage = stringifyBool( food_manage ),
                email = email,
                error_no_name=error_no_name,
                error_no_location=error_no_location,
                error_no_mobile=error_no_mobile,
                error_no_email=error_no_email,
                error_no_craft=error_no_craft,
                error_no_skill=error_no_skill,
                cities=cities,
                suburbs=suburbs,
                locations=locations
                )

class AdminEmployeeDelete(MainHandler):
    def post(self, employee_id):
        employee = model.CapturedEmployee.get_by_id(int(employee_id))

        if employee:
            employee.key.delete()
            utils.decrement_counter("employees")

            self.redirect("/admin/employees")
        else:
            self.redirect("/admin/employee/%s" % employee_id)




# =========================
# Employee Data capture
# =========================

class CheckPostalCode(MainHandler):
    def get(self):
        postal_code = self.request.get("postal_code")
        existing = model.PostalCode.query(model.PostalCode.postal_code == postal_code).fetch()

        area = None
        postal_code_id = None

        if existing:
            area = existing[0].area
            postal_code_id = existing[0].key.id()

        self.render_json({
            "area": area,
            "postal_code_id": postal_code_id
            })

class EmployeeConfirmRedirect(MainHandler):
    def get(self):
        self.redirect("/pubhub/confirm")

class EmployeeConfirm(MainHandler):
    def get(self):
        email = self.request.get("email")
        phone = self.request.get("phone")

        error_no_name = self.request.get("error_no_name")
        error_no_location = self.request.get("error_no_location")
        error_no_mobile = self.request.get("error_no_mobile")
        error_no_email = self.request.get("error_no_email")
        error_no_craft = self.request.get("error_no_craft")
        error_no_skill = self.request.get("error_no_skill")

        cities = model.City.query().order(model.City.city).fetch()
        suburbs = model.Suburb.query().order(model.Suburb.suburb).fetch()

        locations = model.Location.query().fetch()

        self.render("employee-confirm.html", 
            email=email, 
            phone=phone,
            error_no_location=error_no_location,
            error_no_mobile=error_no_mobile,
            error_no_email=error_no_email,
            error_no_craft=error_no_craft,
            error_no_skill=error_no_skill,
            cities=cities,
            suburbs=suburbs,
            locations=locations
            )

    def post(self):

        def boolify(value):
            if value and value == 'yes':
                value = True
            else:
                value = False
            return value

        name = self.request.get("name")
        gender = self.request.get("gender")
        
        postal_code_id = self.request.get("postal_code_id")
        postal_code = self.request.get("postal_code")

        province = ""

        str_postal_code = ""
        if postal_code:
            str_postal_code = postal_code
            province = utils.province_from_code(postal_code)
            # postal_code = int(postal_code)
            # logging.error(province)

        try:
            postal_code = int(postal_code)
        except:
            postal_code = None

        # try:
        #     postal_code = int(postal_code)
        # except:
        #     if postal_code_id:
        #         postal_code_obj = model.PostalCode.get_by_id(int(postal_code_id))
        #         if postal_code_obj:
        #             postal_code = int(postal_code_obj.postal_code)

        city = self.request.get("city")
        can_commute = boolify( self.request.get("can_commute") )
        suburb = self.request.get("suburb")
        
        # bartender = boolify( self.request.get("bartender") )
        # manager = boolify( self.request.get("manager") )
        # waiter = boolify( self.request.get("waiter") )
        # kitchen = boolify( self.request.get("kitchen") )
        # received_training = boolify( self.request.get("received_training") )
        bartender = self.request.get("bartender")
        manager = self.request.get("manager")
        waiter = self.request.get("waiter")
        kitchen = self.request.get("kitchen")
        received_training = self.request.get("received_training")

        phone = self.request.get("phone")

        # canwork = boolify( self.request.get("canwork") )
        canwork = self.request.get("canwork")

        coffee = boolify( self.request.get("coffee") )
        wine = boolify( self.request.get("wine") )
        front_manage = boolify( self.request.get("front_manage") )
        cocktail = boolify( self.request.get("cocktail") )
        silver = boolify( self.request.get("silver") )
        scullery = boolify( self.request.get("scullery") )
        cook = boolify( self.request.get("cook") )
        back_manage = boolify( self.request.get("back_manage") )
        food_manage = boolify( self.request.get("food_manage") )

        reference_name = self.request.get("reference_name")
        reference_duration = self.request.get("reference_duration")
        reference_contact = self.request.get("reference_contact")

        total_skills = 0
        if coffee:
            total_skills += 1
        if wine:
            total_skills += 1
        if front_manage:
            total_skills += 1
        if cocktail:
            total_skills += 1
        if silver:
            total_skills += 1
        if scullery:
            total_skills += 1
        if cook:
            total_skills += 1
        if back_manage:
            total_skills += 1
        if food_manage:
            total_skills += 1

        email = self.request.get("email")

        error_no_name = False
        error_no_location = False
        error_no_mobile = False
        error_no_email = False
        error_no_craft = False
        error_no_skill = False

        error = False

        if name:
            error_no_name = False
        else:
            error_no_name = True
            error = True

        if bartender or manager or waiter or kitchen:
            error_no_craft = False
        else:
            error_no_craft = True
            error = True

        if coffee or wine or front_manage or cocktail or silver or scullery or cook or back_manage or food_manage:
            error_no_skill = False
        else:
            error_no_skill = True
            error = True

        # new
        if not postal_code:
            error_no_location = True
            error = True

        if city or suburb or postal_code_id:
            error_no_location = False
        else:
            error_no_location = True
            error = True

        if not phone:
            error_no_mobile = True
            error = True

        if not email or not utils.valid_email(email):
            error_no_email = True
            error = True

        if email:

            already_captured = model.CapturedEmployee.query(model.CapturedEmployee.email == email).get()

        if not error:
            if not already_captured:

                try:
                    area = utils.area_suburb_from_code(str_postal_code)[0]
                    suburb = utils.area_suburb_from_code(str_postal_code)[1]
                except:
                    logging.error("something went wrong trying to get postal_code object")
                    area = None
                    suburb = None

                ce = model.CapturedEmployee(
                    name=name,
                    gender=gender,
                    postal_code_id=postal_code_id,
                    postal_code=postal_code,
                    area=area,
                    suburb=suburb,
                    province=province,
                    # city=city,
                    # can_commute=can_commute,
                    bartender=bartender,
                    manager=manager,
                    waiter=waiter,
                    kitchen=kitchen,
                    received_training=received_training,
                    phone=phone,
                    canwork=canwork,
                    coffee=coffee,
                    wine=wine,
                    front_manage=front_manage,
                    cocktail=cocktail,
                    silver=silver,
                    scullery=scullery,
                    cook=cook,
                    back_manage=back_manage,
                    food_manage=food_manage,
                    email=email,
                    total_skills=total_skills,
                    reference_name=reference_name,
                    reference_duration=reference_duration,
                    reference_contact=reference_contact
                    )
                ce.put()

                utils.update_counter("employees")

            else:
                try:
                    area = utils.area_suburb_from_code(int(postal_code))[0]
                    suburb = utils.area_suburb_from_code(int(postal_code))[1]
                except:
                    logging.error("something went wrong trying to get postal_code object")
                    area = None
                    suburb = None
                ce = already_captured
                ce.name = name
                ce.gender = gender
                ce.postal_code_id=postal_code_id
                ce.postal_code=postal_code
                ce.area=area
                ce.suburb=suburb
                ce.province=province
                # ce.city=city
                # ce.can_commute=can_commute
                ce.bartender=bartender
                ce.manager=manager
                ce.waiter=waiter
                ce.kitchen=kitchen
                ce.received_training=received_training
                ce.phone=phone
                ce.canwork=canwork
                ce.coffee=coffee
                ce.wine=wine
                ce.front_manage=front_manage
                ce.cocktail=cocktail
                ce.silver=silver
                ce.scullery=scullery
                ce.cook=cook
                ce.back_manage=back_manage
                ce.food_manage=food_manage
                ce.email=email
                ce.total_skills=total_skills
                ce.reference_name=reference_name
                ce.reference_duration=reference_duration
                ce.reference_contact=reference_contact

                ce.put()

            self.redirect("/employee/thank_you?sender_email=%s" % email)

        else:
            def stringifyBool(bool):
                if bool:
                    return "yes"
                else:
                    return ""

            # logging.error("Invalid Form gender: %s" % gender)

            cities = model.City.query().order(model.City.city).fetch()
            suburbs = model.Suburb.query().order(model.Suburb.suburb).fetch()

            locations = model.Location.query().fetch()

            postal_code = None
            if postal_code_id:
                postal_code = model.PostalCode.get_by_id(int(postal_code_id))

            self.render("employee-confirm.html", 
            name = name,
            gender = gender,
            postal_code_id = postal_code_id,
            postal_code=postal_code,
            city = city,
            can_commute = can_commute,
            suburb = suburb,
            # bartender = stringifyBool( bartender ),
            # manager = stringifyBool( manager ),
            # waiter = stringifyBool( waiter ),
            # kitchen = stringifyBool( kitchen ),
            # received_training = stringifyBool( received_training ),
            bartender = bartender,
            manager = manager,
            waiter = waiter,
            kitchen = kitchen,
            received_training = received_training,

            phone = phone,

            # canwork = stringifyBool( canwork ),
            canwork = canwork,

            coffee = stringifyBool( coffee ),
            wine = stringifyBool( wine ),
            front_manage = stringifyBool( front_manage ),
            cocktail = stringifyBool( cocktail ),
            silver = stringifyBool( silver ),
            scullery = stringifyBool( scullery ),
            cook = stringifyBool( cook ),
            back_manage = stringifyBool( back_manage ),
            food_manage = stringifyBool( food_manage ),
            email = email,
            error_no_name=error_no_name,
            error_no_location=error_no_location,
            error_no_mobile=error_no_mobile,
            error_no_email=error_no_email,
            error_no_craft=error_no_craft,
            error_no_skill=error_no_skill,
            cities=cities,
            suburbs=suburbs,
            locations=locations,
            reference_name=reference_name,
            reference_duration=reference_duration,
            reference_contact=reference_contact
            )

class EmployeeThankYou(MainHandler):
    def get(self):

        sender_email = self.request.get("sender_email")

        self.render("thank-you.html", sender_email=sender_email)


class EmployeeReferEmail(MainHandler):
    def post(self):
        sender_email = self.request.get("sender_email")
        recipient_email = self.request.get("recipient_email")

        # mail.send_mail(sender="PubHub <onetwohappiness@gmail.com>",
        #         to="Potential Employee <%s>" % recipient_email,
        #         subject="You've been recommended",
                # body="""
                # Dear Potential Employee:<br>

                # A friend of yours has recommended that you complete <a href="http://staging-one.appspot.com/employee/confirm" target="_blank>this form</a>
                # so that you can feature in the new PubHub app, where bar and restaurant owners from all over South Africa can find you.<br><br>

                # Please let us know if you have any questions.<br>

                # The PubHub Team
                # """)
    
        
        body="""
            Dear Potential Employee:<br>

            A friend of yours ( %s ) has recommended that you complete <a href="http://pubhub.co.za/employees/confirm" target="_blank>this form</a>
            so that you can feature in the new PubHub app, where bar and restaurant owners from all over South Africa can find you.<br><br>

            Please let us know if you have any questions.<br>

            The PubHub Team
            """ % sender_email

        body="""
            Dear Potential Employee, 
            A friend of yours ( %s ) has recommended that you complete the form at: http://pubhub.co.za/employees/confirm
            so that you can feature in the new PubHub app, where bar and restaurant owners from all over South Africa can find you.

            Fill in your details accurately, and we'll connect you with bar owners that need your skills.

            Please let us know if you have any questions.
            The PubHub Team
            """ % sender_email

        text="""
            Dear Potential Employee, 
            A friend of yours ( %s ) has recommended that you complete the form at: http://pubhub.co.za/employees/confirm
            so that you can feature in the new PubHub app, where bar and restaurant owners from all over South Africa can find you.

            Fill in your details accurately, and we'll connect you with bar owners that need your skills.
            
            Please let us know if you have any questions.
            The PubHub Team
            """ % sender_email

        
        try:
            message = mail.EmailMessage(sender="PubHub <pubhubza@gmail.com>",
                                    subject="You've been recommended")
            message.to = recipient_email
            message.html = body
            message.send()
            utils.update_counter("referrals")
        except:
            try:
                # fallback is mandrill
                utils.send_mandrill_mail("You've been recommended", body, text, recipient_email)
            except:
                logging.error("couldnt send gmail... probably invalid email")



        # logging.error("NEED TO SETUP MANDRILL EMAIL SENDING")
        self.render_json({
            "message": "success",
            "long_message": "message sent"
            })



# =========================
# User Online Dashboard
# =========================

class UserProfile(MainHandler):
    def get(self):

        user_obj = self.user

        # ===============
        # Check if user is still valid
        # ===============
        now = datetime.datetime.now()
        if user_obj and user_obj.period_end:
            if user_obj.period_end <= now:
                user.paid = False
                user.put()

        error = self.request.get("error")

        error_message = ""
        if error == "email_exists":
            error_message = "Could not update your email please ensure that it isn't already registered on the system"

        if user_obj:
            brand = None
            exp_month = None
            exp_year = None
            last4 = None
            if user_obj.stripeCustomer:
                stripeCustomer = json.loads(json.dumps(user_obj.stripeCustomer))
                brand = stripeCustomer["sources"]["data"][0]["brand"]
                exp_month = stripeCustomer["sources"]["data"][0]["exp_month"]
                exp_year = stripeCustomer["sources"]["data"][0]["exp_year"]
                last4 = stripeCustomer["sources"]["data"][0]["last4"]
            self.render("user-profile.html", user_obj=user_obj, error_message=error_message, last4=last4, brand=brand, exp_month=exp_month, exp_year=exp_year)
        else:
            self.redirect("/login")

    def post(self):
        name = self.request.get("name")
        fname = self.request.get("fname")
        lname = self.request.get("lname")
        postal_code = self.request.get("postal_code")
        email = self.request.get("email")
        userID = self.request.get("userID")

        error = False
        if userID:
            user = model.User.get_by_id(int(userID))

            if user:
                user.name = name
                user.fname = fname
                user.lname = lname

                if postal_code:
                    utils.check_postal_code(user, postal_code)
                    user.postal_code = postal_code

                if email:
                    if utils.check_email(user, email):
                        user.email = email
                        error = True

                if not error:
                    user.put()
                    self.redirect("/user/profile")
                else:
                    self.redirect("/user/profile?error=email_exists")


# =========================
# Payments
# =========================

class GetToken(MainHandler):
    def get(self):
        token = utils.generate_random_token(6)
        token_count = model.TokenCount.query().get()
        if not token_count:
            token_count = model.TokenCount()
            token_count.put()

        token = token + str(token_count.count)
        token_count.count += 1
        token_count.put()

        self.render_json({
            "token": token
            })

class CheckUsedToken(MainHandler):
    def get(self):
        token = self.request.get("token")
        existing_token = model.UsedToken.query(model.UsedToken.token==token).get()

        if existing_token:
            result = True
            token = existing_token.token
            purchased = existing_token.purchased
            if existing_token.payment:
                payment_id = existing_token.payment.id()
            else:
                payment_id = False
        else:
            result = False
            purchased = False
            payment_id = False

        # can later include the number of tokens purchased... and soem other payment details
        self.render_json({
            "result": result,
            "token": token,
            "purchased": purchased,
            "payment_id": payment_id
            })

class PayTest(MainHandler):
    def get(self):
        year = datetime.datetime.now().year
        # token = utils.generate_random_token(6)
        token = self.request.get("token")

        userID = self.request.get("userID")

        if userID:
            user = model.User.get_by_id(int(userID))

            # token_count = model.TokenCount.query().get()
            # if not token_count:
            #     token_count = model.TokenCount()
            #     token_count.put()

            # token = token + str(token_count.count)
            # token_count.count += 1
            # token_count.put()

            email = user.email
            user_id = userID
            name = user.name
            fname = user.fname
            lname = user.lname

            if not fname and not lname:
                fname = 'GHR User'
                lname = userID

            base_url = "http://%s.appspot.com" % utils.app_id
            # base_url = "http://127.0.0.1:8080"

            if token:
                self.render("pay-test.html", year=year, token=token, userID=userID, base_url=base_url, fname=fname, lname=lname, email=email)
            else:
                # self.response.out.write("sorry no valid token was found")
                logging.error("... no valid token")
                self.render("pay-error.html")

        else:
            # self.response.out.write("sorry not a valid user")
            logging.error("... no valid user")
            self.render("pay-error.html")

class PayTestNotify(MainHandler):
    def get(self):
        logging.error("LOG POST RESPONSE - - - - - - - - - GET")
        logging.error(self.request.body)
    def post(self):
        logging.error("LOG POST RESPONSE - - - - - - - - - POST")
        logging.error(self.request.body)

        m_payment_id = self.request.get("m_payment_id")
        pf_payment_id = self.request.get("pf_payment_id")
        payment_status = self.request.get("payment_status")
        item_name = self.request.get("item_name")
        item_description = self.request.get("item_description")
        amount_gross = self.request.get("amount_gross")
        amount_fee = self.request.get("amount_fee")
        amount_net = self.request.get("amount_net")
        custom_int1 = self.request.get("custom_int1")
        custom_str1 = self.request.get("custom_str1")
        name_first = self.request.get("name_first")
        name_last = self.request.get("name_last")
        email_address = self.request.get("email_address")
        merchant_id = self.request.get("merchant_id")
        signature = self.request.get("signature")
        # Pass the registered client email as custom_str2
        userID = self.request.get("custom_str2")

        logging.error("custom_str2")
        logging.error(userID)

        user = model.User.get_by_id(int(userID))
        
        user.paid = True
        user.date_paid = datetime.datetime.now()
        user.put()

        logging.error("is user updated?")
        logging.error(user.paid)
        logging.error(user.date_paid)


        payment_record = model.PayfastPayment(
            m_payment_id=m_payment_id,
            pf_payment_id=pf_payment_id,
            payment_status=payment_status,
            item_name=item_name,
            item_description=item_description,
            amount_gross=amount_gross,
            amount_fee=amount_fee,
            amount_net=amount_net,
            custom_int1=custom_int1,
            custom_str1=custom_str1,
            name_first=name_first,
            name_last=name_last,
            email_address=email_address,
            merchant_id=merchant_id,
            signature=signature,
            user=user.key,
            )

        payment_record.put()

        used_token = model.UsedToken(token=custom_str1, payment=payment_record.key, purchased=True)
        used_token.put()

        self.render_json({
            "message": "success"
            })

class PayTestSuccess(MainHandler):
    def get(self):
        self.render("pay-success.html")

class PayTestCancel(MainHandler):
    def get(self):
        token = self.request.get("token")
        if token:
            used_token = model.UsedToken(token=token)
            used_token.put()
        # self.response.out.write("you've cancelled your payment... no worries")
        logging.error("... payment cancelled")
        self.render("pay-cancel.html")


class StripeCheckCoupon(MainHandler):
    def get(self, coupon):
        stripe.api_key = utils.stripe_api_key
        
        logging.error(" . . . . . . . . coupon list")
        logging.error(stripe.Coupon.all(limit=99))
        coupons_resp = stripe.Coupon.all(limit=99)
        coupons = coupons_resp.data
        logging.error(coupons)

        coupon_list = []
        for c in coupons:
            coupon_list.append(c.id)

        if coupon in coupon_list:
            coupon_obj = stripe.Coupon.retrieve(coupon)
            if coupon_obj.valid:
                self.render_json({
                    "message": "success",
                    "valid": True,
                    "coupon": coupon,
                    "percent_off": coupon_obj.percent_off,
                    "amount_off": coupon_obj.amount_off,
                    "currency": coupon_obj.currency,
                    "duration": coupon_obj.duration
                    })
            else:
                self.render_json({
                    "message": "success",
                    "valid": False,
                    "coupon": coupon,
                    "percent_off": coupon_obj.percent_off,
                    "amount_off": coupon_obj.amount_off,
                    "currency": coupon_obj.currency,
                    "duration": coupon_obj.duration
                    })
        else:
            self.render_json({
                "message": "success",
                "valid": False,
                "coupon": coupon,
                })

class PayStripe(MainHandler):
    def get(self):
        userID = self.request.get("userID")
        user_obj = model.User.get_by_id(int(userID))

        subscription_valid = False
        subscription_end = False
        trial_end = ''
        if user_obj:
            if user_obj.stripeCustomer:
                subscription_end = json.loads(json.dumps(user_obj.stripeCustomer))["subscriptions"]["data"][0]["current_period_end"]
                now = datetime.datetime.now()
                subscription_end = datetime.datetime.fromtimestamp(subscription_end)

                logging.error("NOW: %s" % now)
                logging.error("subscription_end: %s" % subscription_end)

                if subscription_end > now:
                    subscription_valid = True
                    trial_end = subscription_end.strftime("%d/%m/%y")

        self.render("pay-stripe.html", userID=userID, user_obj=user_obj, subscription_end=subscription_end, subscription_valid=subscription_valid, trial_end=trial_end)

    def post(self):
        logging.error("GOT RESPONSE FROM STRIPE")

        logging.error(self.request)

        stripeToken = self.request.get("stripeToken")
        submitted = self.request.get("submitted")
        userID = self.request.get("userID")
        coupon = self.request.get("coupon")

        logging.error("....................................")
        logging.error("stripeToken: %s" % stripeToken)
        logging.error("submitted: %s" % submitted)
        logging.error("Coupon: %s" % coupon)

        if userID:
            user = model.User.get_by_id(int(userID))
            if stripeToken:
                # Set your secret key: remember to change this to your live secret key in production
                # See your keys here https://dashboard.stripe.com/account/apikeys
                stripe.api_key = utils.stripe_api_key
                
                user.stripeToken = stripeToken
                #user.put()# added .put() later

                existing_plan = model.SubscriptionPlan.query().get()

                subscription_plan_name = 'TGH Recruitment Plan'
                subscription_plan_id = 'tghr_basic'

                if not existing_plan:
                    # double check that plan doesn't exist
                    try:
                        created_plan = stripe.Plan.retrieve("tghr_basic")
                        if created_plan and not existing_plan:
                            existing_plan = model.SubscriptionPlan().put()
                    except Exception as e:
                        logging.error("something went wrong checking if Stripe subscription plan exists")
                        logging.exception(e)
                        try:
                            #==================================
                            #  create stripe subscription plan
                            # =================================
                            stripe.Plan.create(
                              amount=31500,
                              interval='month',
                              name=subscription_plan_name,
                              currency='zar',
                              id=subscription_plan_id)
                            existing_plan = model.SubscriptionPlan().put()
                        except:
                            logging.error("something went wrong trying to create a Stripe subscription plan")

                    if not created_plan:
                        try:
                            #==================================
                            #  create stripe subscription plan
                            # =================================
                            stripe.Plan.create(
                              amount=31500,
                              interval='month',
                              name=subscription_plan_name,
                              currency='zar',
                              id=subscription_plan_id)
                            existing_plan = model.SubscriptionPlan().put()
                        except:
                            logging.error("something went wrong trying to create a Stripe subscription plan")

                #==================================
                #  associate subscription plan with a customer
                # =================================

                # Get the credit card details submitted by the form
                token = stripeToken# request.POST['stripeToken']

                if not coupon:
                    coupon = None
                    # Create a Customer
                    customer = stripe.Customer.create(
                      source=token,
                      plan="tghr_basic",
                      email=user.email
                    )
                else:
                    try:
                        coupon_obj = stripe.Coupon.retrieve(coupon)
                        if coupon_obj.valid:
                            # Create a Customer
                            customer = stripe.Customer.create(
                              source=token,
                              plan="tghr_basic",
                              email=user.email,
                              coupon=coupon
                            )
                        else:
                            customer = stripe.Customer.create(
                              source=token,
                              plan="tghr_basic",
                              email=user.email
                            )
                    except:
                        logging.error("somethign went wrong with a coupon subscription payment")
                # customer = stripe.Customer.create(
                #   source=token,
                #   plan="tghr_basic",
                #   email=user.email
                #   coupon="coupon_ID"# PubhubFreeMonth
                # )
                
                logging.error("STRIPE customer.....")
                logging.error(customer)

                user.stripeCustomer = customer
                user.stripeCustomerID = customer.id
                user.paid = True
                user.paying = False
                user.date_paid = datetime.datetime.now()
                user.put()

                utils.update_counter("clients")

                # SEND RECEIPT EMAIL HERE.....

                logging.info("Customer created")
                logging.info(customer)

        # self.response.set_status(200)
        self.render("pay-success.html")

class CancelStripeSubscription(MainHandler):
    def post(self):
        userID = self.request.get("userID")
        user = model.User.get_by_id(int(userID))
        stripe.api_key = utils.stripe_api_key
        stripe_customer_id = json.loads(json.dumps(user.stripeCustomer))["id"]
        customer = stripe.Customer.retrieve(stripe_customer_id)

        logging.error("customer . . . . ")
        logging.error(customer)

        subscription_id = json.loads(json.dumps(user.stripeCustomer))['subscriptions']['data'][0]['id']

        customer.subscriptions.retrieve(subscription_id).delete(at_period_end=True)

        user.paid = False
        user.paying = False
        user.put()

        utils.update_counter("cancellations")

        self.render("pay-cancel.html")

class APICancelStripeSubscription(MainHandler):
    def post(self):
        from_web = self.request.get("from_web")
        userID = self.request.get("userID")
        password = self.request.get("password")
        user = model.User.get_by_id(int(userID))

        if from_web == "yes":
            if self.user:
                if not user.date_cancelled:
                    period_end = utils.unsubscribe_user(user)#datetime obj
                    if period_end:
                        end_date = period_end.strftime("%d/%m/%y")
                        self.render("pay-cancel.html")
                    else:
                        self.render("pay-cancel.html")
                else:
                    self.render("pay-cancel.html")
            else:
                self.redirect("/login")

        else:
            if user and utils.confirm_password(user, password):
                if not user.date_cancelled:

                    period_end = utils.unsubscribe_user(user)#datetime obj

                    if period_end:
                        end_date = period_end.strftime("%d/%m/%y")

                        self.render_json({
                            "message": "Your subscription to Pubhub has been cancelled, the service will continue until %s." % end_date,
                            "invalidPassword": False,
                            "invalidUser": False
                        })
                    else:
                        self.render_json({
                        "message": "You're not yet subscribed to Pubhub.",
                        "invalidPassword": False,
                        "invalidUser": False
                    })
                else:
                    end_date = user.period_end.strftime("%d/%m/%y")
                    self.render_json({
                        "message": "Your subscription to Pubhub has already been cancelled, the service will continue until %s." % end_date,
                        "invalidPassword": False,
                        "invalidUser": False
                    })
            else:
                self.render_json({
                    "message": "Invalid Password, if you continue to encounter problems, please contact support@pubhub.co.za",
                    "invalidPassword": True,
                    "invalidUser": True
                })

class CancelStripePayment(MainHandler):
    def post(self):
        userID = self.request.get("userID")
        user = model.User.get_by_id(int(userID))

        if user:
            user.paying = False
            user.put()

        self.render("pay-cancel.html")

class APIGetStripePublishableKey(MainHandler):
    def get(self):
        userID = self.request.get("userID")

        #"pk_test_FIRsKqxO3UC3E6qz2bknorgh"
        self.render_json({
            "key": utils.stripe_publishable_key
            })

class StripeWebhook(MainHandler):
    def post(self):
        logging.error(self.request.body)
        event_json = json.loads(self.request.body)
        logging.error("...........STRIPE WEBHOOK DATA...........")

        # WEBHOOK EVENT TYPES TO CHECK FOR

        # charge.captured
        # charge.failed
        # charge.refunded
        # charge.succeeded
        # charge.updated

        # coupon.created
        # coupon.deleted
        # coupon.updated

        # customer.created
        # customer.deleted
        # customer.updated

        # customer.discount.created# when a coupon is attached to a customer
        # customer.discount.deleted
        # customer.discount.updated

        # customer.subscription.created
        # customer.subscription.deleted
        # customer.subscription.trial_will_end
        # customer.subscription.updated# when a subscription changes, i.e. move to be pending to be cancelled

        # # for subscription payments
        # invoice.created# stripe waits for webhooks to be processed for 3 days after that it will try to pay the invoice regardless
        # invoice.payment_failed
        # invoice.payment_succeeded
        # invoice.updated

        # TO DO
        # First payment is processed
        # Any subsequent payment is processed
        # n/a User changes subscription level
        # User updates credit card information
        # User or admin cancels account
        # Application of a promotional voucher
        # Credit card information is no longer valid


        # ==================
        # events and process of interest
        # ==================

        # - - -User adds card and signs up for the subscription
        # customer.created (Customer )
        # customer.card.created (Card )
        # customer.subscription.created (Subscription )
        # invoice.created (Invoice )
        # invoice.payment_succeeded (Invoice )
        # charge.succeeded

        # - - -User's regular monthly payment goes through
        # invoice.created (Invoice )
        # invoice.payment_succeeded (Invoice )
        # charge.succeeded

        # - - -User's charge attempt fails
        # invoice.payment_failed (Invoice )
        # charge.failed (Charge )
        # customer.subscription.updated (Subscription )
        # customer.updated

        # - - -After 3 attempts to charge the card the subscription is cancelled
        # customer.subscriptions.deleted




        def timestamp_to_readable_date(timestamp):
            return datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')


        #================================
        # First payment is processed
        #================================
        #if event_json["type"] == "charge.succeeded":
        if event_json["type"] == "customer.subscription.created":

            if event_json["data"]:
                if event_json["data"]["object"]["current_period_end"]:
                    period_start = event_json["data"]["object"]["current_period_start"]
                    period_end = event_json["data"]["object"]["current_period_end"]
                    amount = event_json["data"]["object"]["plan"]["amount"]

                    logging.error("Charge succeeded... first subscription payment completed?")
                    logging.error("period start: %s period end: %s" % (timestamp_to_readable_date(period_start), timestamp_to_readable_date(period_end)))
                    logging.error("JOINED: Thank you for joining Pubhub and for your payment, you will be charged again on the %s for an amount of %s" % (timestamp_to_readable_date(period_end), amount))
                    
                    # SEND NOTIFICATION EMAIL
                    # need to get customer_id
                    customer_id = event_json["data"]["object"]["customer"]
                    user = model.User.query(model.User.stripeCustomerID == customer_id).get()
                    if user:
                        name = ""
                        if user.name:
                            name = user.name
                        # utils.send_mandrill_mail("subscribed", user.email)
                        emails.render_and_send_email_template("subscribed", user.email, name=name)
                else:
                    logging.error("No json parse problem - A")
            else:
                logging.error("No json parse problem - Aa")

        #================================
        # Subsequent payment is processed
        #================================
        # if event_json["type"] == "charge.succeeded":# charge.succeeded doesn't have the current_period_end data
        if event_json["type"] == "invoice.payment_succeeded":
            if event_json["data"]:
                period_start = event_json["data"]["object"]["lines"]["data"][0]["period"]["start"]
                period_end = event_json["data"]["object"]["lines"]["data"][0]["period"]["end"]
                amount = event_json["data"]["object"]["lines"]["data"][0]["plan"]["amount"]

                logging.error("Charge succeeded...")
                logging.error("Thank you for your payment, you will be charged again on the %s for an amount of %s" % (timestamp_to_readable_date(period_end), amount))

                # SEND NOTIFICATION EMAIL
                # need to get customer_id
                customer_id = event_json["data"]["object"]["customer"]
                user = model.User.query(model.User.stripeCustomerID == customer_id).get()
                if user:
                    name = ""
                    if user.name:
                        name = user.name
                    # utils.send_mandrill_mail("successful_payment", user.email)
                    emails.render_and_send_email_template("successful_payment", user.email, name=name)
            else:
                logging.error("No json parse problem - B")

        #================================
        # Update Credit Card
        #================================
        # Don't need to notify a user that a new card has been added, they'll get confirmation when they perfom the change
        #create a new card then delete then set the new card to the default card, alternatively just delete the old card

        #================================
        # Invalid Credit Card details
        #================================
        if event_json["type"] == "invoice.payment_failed":
            # this will be fired each time stripe tries to charge card adn it fails... can prompt user to update credit card here
            if event_json["data"]:
                logging.error("DATA... from payment failed")
                logging.error(event_json["data"])
                logging.error("Payment FAILED... card cancelled or something... send notification email")
                # SEND NOTIFICATION EMAIL
                # need to get customer_id
                customer_id = event_json["data"]["object"]["customer"]
                user = model.User.query(model.User.stripeCustomerID == customer_id).get()
                if user:
                    name = ""
                    if user.name:
                        name = user.name
                    # utils.send_mandrill_mail("failed_payment", user.email)
                    emails.render_and_send_email_template("failed_payment", user.email, name=name)
            else:
                logging.error("No json parse problem D")

        #================================
        # Cancellation of a subscription After Multiple retries ( 3 times ) the subscription will be cancelled
        #================================
        if event_json["type"] == "customer.subscription.deleted":
            if event_json["data"]:
                if event_json["data"]["object"]["current_period_end"]:
                    period_start = event_json["data"]["object"]["current_period_start"]
                    period_end = event_json["data"]["object"]["current_period_end"]
                    amount = event_json["data"]["object"]["plan"]["amount"]

                    logging.error("Cancelled subscription")
                    logging.error("We're sorry to see you go, the pubhub service will end at: %s and your last bill will be for: %s" % (timestamp_to_readable_date(period_end), amount))
                    logging.error("We're sorry to see you go, the pubhub service will end at: %s ( don't mention last bill because if subscription was deleted because of a failed payments then there will be no last charge )" % timestamp_to_readable_date(period_end))
                    
                    customer_id = event_json["data"]["object"]["customer"]
                    user = model.User.query(model.User.stripeCustomerID == customer_id).get()

                    if user:
                        user.period_end = datetime.datetime.fromtimestamp(int(period_end))
                        user.put()
                        # SEND NOTIFICATION EMAIL
                        # need to get customer_id
                        if user:
                            name = ""
                            if user.name:
                                name = user.name
                            # utils.send_mandrill_mail("cancelled_subscription", user.email)
                            emails.render_and_send_email_template("cancelled_subscription", user.email, name=name)

                else:
                    logging.error("No json parse problem - C")
            else:
                logging.error("No json parse problem - Ca")

            # need to:
            # update the user on DB, remove references to Stripe
            # potentially delete the customer from stripe
            # allow customer to rejoin with new payment details


        #  invoice.payment_failed
        # customer.subscriptions.deleted # <-- need to go into stripe settings to set what happens after caredit card charge doesn't go through after 3rd attempt
        #    --- address to set this: : https://manage.stripe.com/#account/recurring



# ============== exception
        #try:

        # logging.error(event_json)
        # logging.error(event_json["type"])

        # period_start = "NOTHING START"
        # period_end = "NOTHING END"
        # amount = "NOTHING AMOUNT"

        # if event_json["type"] == "invoice.payment_succeeded":
        #     logging.error(event_json["data"])
        #     logging.error(event_json["data"]["object"]["period_end"])
        #     if event_json["data"]["object"]["period_end"] and event_json["data"]["object"]["total"]:
        #         period_start = event_json["data"]["object"]["period_start"]
        #         period_end = event_json["data"]["object"]["period_end"]
        #         amount = event_json["data"]["object"]["total"]

        #     logging.error("Subscription payment succeeeded, send a confirmation email and remind about the date of the next invoice payment...")
        #     logging.error("MONTHLY PAYMENT: Thank you for your payment, you will be charged again on the %s for an amount of %s" % (timestamp_to_readable_date(period_end), amount))

        # if event_json["type"] == "customer.subscription.updated":
        #     if event_json["data"]["object"]["cancel_at_period_end"]:
        #         logging.error("email user that their subscription is set to be cancelled at the period end: %s" % timestamp_to_readable_date(period_end))
        #         logging.error("CANCELLED: We're sorry to see you leave you will no longer be charged after this billing period, your service will continue until: %s you will still be charged for this period for an amount of %s" % (timestamp_to_readable_date(period_end), amount))
        #     else:
        #         logging.error("no cancel_at_period_end . . . .  so must be some other kind of update")



        # =================================
        # Save Stripe Event to DB
        # =================================
        # customer_id = ""
        # userID = ""
        # user = None
        # if event_json["data"]:
        #     logging.error("... has data and wants to save to DB")
        #     logging.error(event_json["data"])
        #     logging.error(event_json["data"]["object"])
        #     logging.error(event_json["data"]["object"]["customer"])
        #     if event_json["data"]["object"]["customer"]:
        #         logging.error("... there is a customer and wants to save to DB")
        #         customer_id = event_json["data"]["object"]["customer"]
        #         logging.error("... customer ID: %s" % customer_id)
                
        #         user = model.User.query(model.User.stripeCustomerID == customer_id).get()
                
        #         if user:
        #             userID = str( user.key.id() )

        # stripe_event = model.StripeEvent( event=json.dumps( self.request.body ), event_type=event_json['type'], customer_id=customer_id, userID=userID )
        # stripe_event.put()

        # if stripe_event:
        #     logging.error("has it saved to DB?????? %s" % stripe_event.key.id())
        # else:
        #     logging.error(".... there is no stripe_event")

# ============== exception
        # except:
        #     logging.error("couldn't read the response")

        self.response.set_status(200)


# =========================
# Mobile API
# =========================

class APIRegister(MainHandler):
    def post(self):
        # name = self.request.get('name')
        email = self.request.get('email')
        password = self.request.get('password')
        verify_password = self.request.get('verify_password')
        location_id = self.request.get('location_id')
        postal_code = self.request.get('postal_code')
        key = self.request.get('key')

        location = False
        logging.error("postal_code........")
        logging.error(postal_code)

        error = False
        error_name = ""
        error_password = ""
        error_email = ""
        error_verify = ""
        error_postal_code = ""

        error_flag_name = False
        error_flag_password = False
        error_flag_email = False
        error_flag_verify = False
        error_flag_postal_code = False


        error_msg = {};
        user = None
            
        if not utils.valid_password(password):
            error_password="Your password needs to be between 3 and 20 characters long"
            error = True
            logging.error("pw error ........")
            error_flag_password = True
            
        if not utils.valid_email(email):
            error_email="Please type in a valid email address"
            error = True
            logging.error("email error ........")
            error_flag_email = True
            
        if password != verify_password:
            error_verify="Please ensure your passwords match"
            error = True
            logging.error("pw verify error ........")
            error_flag_verify = True

        province = ""
        if postal_code:
            existing = model.PostalCode.query(model.PostalCode.postal_code == postal_code).fetch()
            if not existing:
                error = True
                logging.error("post code error ........")
                error_postal_code="Please ensure you include a valid postal code"
                error_flag_postal_code = True
            else:
                province = utils.province_from_code(postal_code)
        else:
            error = True
            error_postal_code="Please ensure you include a postal code"
            error_flag_postal_code = True
        
        if not error:
            logging.error("no error ........")
            pw_hash = utils.make_pw_hash(email, password)
            # user = model.User(parent=model.users_key(), name=name, email=email, pw_hash=pw_hash)
            user = model.User.query(model.User.email == email).get()
            if not user:
                user = model.User( email=email, pw_hash=pw_hash, postal_code=postal_code, province=province)
                user.put()
                logging.error("SEND EMAIL - CONFIRMATION OF REGISTRATION")
                # utils.send_mandrill_mail(subject, html, text, to_email)
                # utils.send_mandrill_mail("registration", email)
                name = ""
                if user.name:
                    name = user.name
                if user.email:
                    emails.render_and_send_email_template("registration", user.email, name=name)

                utils.update_counter("registrations")

            
        else:
            logging.error("error ........")
            error_msg = {
                'error_password':error_password,
                'error_email':error_email,
                'error_verify':error_verify,
                'error_postal_code':error_postal_code,
            }

        if user:
            self.render_json({
                "userID": user.key.id(),
                "paid": user.paid,
                "message": "success",
                "error_msg": error_msg,
                "error_flag_password": error_flag_password,
                "error_flag_email": error_flag_email,
                "error_flag_verify": error_flag_verify,
                "error_flag_postal_code": error_flag_postal_code
            })
        else:
            self.render_json({
                "userID": None,
                "paid": None,
                "message": "success",
                "error_msg": error_msg,
                "error_flag_password": error_flag_password,
                "error_flag_email": error_flag_email,
                "error_flag_verify": error_flag_verify,
                "error_flag_postal_code": error_flag_postal_code
            })

class APILogin(MainHandler):
    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        user = model.User.login(email, password)
        if user:
            self.login(user)
            self.render_json({
                "userID": user.key.id(),
                "paid": user.paid,
                "message": "success"
            })
        else:
            self.render_json({
                "userID": "",
                "message": "invalid email / password"
            })

class APIForgotPassword(MainHandler):
    def get(self):
        email = self.request.get("email")

        user = model.User.query(model.User.email == email).get()

        if user:
            new_pw = utils.generate_random_token(5)
            new_pw_hash = utils.make_pw_hash(email, new_pw)
            user.pw_hash = new_pw_hash
            user.put()

            # email_obj = emails.get_email_template("forgot_password", (), (new_pw), (new_pw))
            # utils.send_mandrill_mail_template(email_obj, email)

            emails.render_and_send_email_template("forgot_password", user.email, name=user.name, new_pw=new_pw)

            self.render_json({
                "email": email,
                "invalidEmail": False,
                "message": "A temporary Password has been sent to %s" % email
                })
        else:
            self.render_json({
                "email": email,
                "invalidEmail": True,
                "message": "Sorry there is no user with the email address %s" % email
                })

class APICandidate(MainHandler):
    def get(self):
        userID = self.request.get("userID")
        email = self.request.get("email")

        paying_user = False
        user = None
        province = ''

        try:
            user = model.User.get_by_id(int(userID))
            province = user.province
            if user.email == email and user.paid:
                paying_user = True

            # logging.error("user details")
            # logging.error("user.email: %s" % user.email)
            # logging.error("email: %s" % email)
            # logging.error("user.paid: %s" % user.paid)
        except:
            logging.error("no user found")

        skills = self.request.get("skills")
        postal_code = None

        # ===============
        # Check if user is still valid
        # ===============
        now = datetime.datetime.now()
        if user and user.period_end:
            if user.period_end <= now:
                user.paid = False
                user.put()

        if user:
            if user.postal_code:
                try:
                    postal_code = user.postal_code
                    logging.error("postal_code in try catch . . . . . . . ")
                    logging.error(postal_code)
                except:
                    region = None

        if skills:
            skills = skills.split(",")
            skills = filter(None, skills)

        if len(skills) <= 0:
            skills = False

        # ===================================
        # build the query
        # ===================================
        
        curs = Cursor(urlsafe=self.request.get('cursor'))
        q = model.CapturedEmployee.query()
        if skills and len(skills) > 0:
            for s in skills:
                logging.error("Skilllllssssss . . . . . . . . . . . ")
                logging.error(s)
                try:
                    q = q.filter(getattr(model.CapturedEmployee, s) == 'yes')
                except:
                    logging.error("error")

        num_candidates = 20

        logging.error(" - - - - - - - - - - - is there a postal code and province???")
        logging.error(postal_code)
        logging.error(province)

        if postal_code and province:
            # CLOSE
            curs_close = Cursor(urlsafe=self.request.get('cursor_close'))
            candidates_close, next_curs_close, more_close = q.filter(model.CapturedEmployee.postal_code == int(postal_code)).order(-model.CapturedEmployee.total_skills).fetch_page(num_candidates, start_cursor=curs_close)
            # PROVINCE
            curs_province = Cursor(urlsafe=self.request.get('cursor_province'))
            candidates_province, next_curs_province, more_province = q.filter(model.CapturedEmployee.province == province).order(-model.CapturedEmployee.total_skills).fetch_page(num_candidates, start_cursor=curs_province)
        else:
            candidates_close = []
            candidates_province = []

        # EVERYONE
        candidates, next_curs, more = q.order(-model.CapturedEmployee.total_skills).fetch_page(num_candidates, start_cursor=curs)

        logging.error("------------------ candidates")
        logging.error(len(candidates))

        # candidates, next_curs, more = q.order(model.Employee._key, model.Employee.name).fetch_page(50, start_cursor=curs)
        # candidates, next_curs, more = model.Employee.query(model.Employee.active==True, model.Employee.coffee == True).order(model.Employee.name).fetch_page(500, start_cursor=curs)

        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False

        candidate_list = []

        candidate_ids = []

        # logging.error("User province")
        # logging.error(province)
        # logging.error("User postal_code")
        # logging.error(postal_code)
        # logging.error(candidates_close)

        # this relies on candidate_ids being filled, i.e. that array is not passed to the definition/function
        def fill_candidate_list(candidates, candidate_list, search_type):
            for c in candidates:
                candidate = {}
                candidate_id = c.key.id()
                if candidate_id not in candidate_ids:
                    candidate_ids.append(candidate_id)

                    candidate["name"] = c.name
                    candidate["id"] = c.key.id()
                    candidate["area"] = c.area
                    candidate["suburb"] = c.suburb

                    # changed when making the app free

                    # if paying_user:
                    #     candidate["email_contact"] = c.email
                    #     candidate["phone_contact"] = c.phone
                    # else:
                    #     candidate["email_contact"] = ""
                    #     candidate["phone_contact"] = ""

                    # added the 2 lines below when making the app free
                    candidate["email_contact"] = c.email
                    candidate["phone_contact"] = c.phone


                    candidate["coffee"] = c.coffee
                    candidate["wine"] = c.wine
                    candidate["front_manage"] = c.front_manage
                    candidate["cocktail"] = c.cocktail
                    candidate["silver"] = c.silver
                    candidate["scullery"] = c.scullery
                    candidate["cook"] = c.cook
                    candidate["back_manage"] = c.back_manage
                    candidate["food_manage"] = c.food_manage
                    candidate["search_type"] = search_type

                    skill_list = []
                    if candidate["coffee"]:
                        skill_list.append("Coffee")
                    if candidate["wine"]:
                        skill_list.append("Wine")
                    if candidate["front_manage"]:
                        skill_list.append("FOH Manager")
                    if candidate["cocktail"]:
                        skill_list.append("Cocktail")
                    if candidate["silver"]:
                        skill_list.append("Silver Service")
                    if candidate["scullery"]:
                        skill_list.append("Scullery")
                    if candidate["cook"]:
                        skill_list.append("Chef/Cooking")
                    if candidate["back_manage"]:
                        skill_list.append("BOH Manager")
                    if candidate["food_manage"]:
                        skill_list.append("Food + Bev Manager")

                    candidate["skill_list"] = skill_list
                    candidate["received_training"] = c.received_training
                    candidate["canwork"] = c.canwork
                    candidate["province"] = c.province
                    candidate["postal_code"] = c.postal_code
                    candidate["reference_name"] = c.reference_name
                    candidate["reference_duration"] = c.reference_duration
                    candidate["reference_contact"] = c.reference_contact

                    candidate_list.append(candidate)

        # only populate the close and province search results for the first query... so only when there isn't a curs
        
        # fill_candidate_list(candidates_close, candidate_list, "postal_code_match")
        # fill_candidate_list(candidates_province, candidate_list, "province_match")
        # fill_candidate_list(candidates, candidate_list, "skill_match")

        cursor_in_request = self.request.get("cursor")
        if not cursor_in_request:
            fill_candidate_list(candidates_close, candidate_list, "postal_code_match")
            fill_candidate_list(candidates_province, candidate_list, "province_match")
            fill_candidate_list(candidates, candidate_list, "skill_match")
            # logging.error("..............not curs..............")
        else:
            fill_candidate_list(candidates, candidate_list, "skill_match")
            # logging.error("..............is curs..............")
            # logging.error(cursor_in_request)


        # candidate_list = sorted(candidate_list, key=itemgetter('name'), reverse=False)

        # set curs to false for javascript purposes in app
        if not curs:
            curs = False
        else:
            curs = curs.urlsafe()

        paid_flag = False
        if user:
            # removed the below 2 lines when making free
            # if user.paid:
            #     paid_flag = True

            # added the below 1 line when making free
            paid_flag = True



        self.render_json({
            "candidates": candidate_list,
            "results": len(candidate_list),
            "paid": paid_flag,
            "next_curs": next_curs,
            "prev_curs": curs
            })

class APIUserPaid(MainHandler):
    def get(self):
        userID = self.request.get("userID")

        user = model.User.get_by_id(int(userID))

        paid = False

        # ===============
        # Check if user is still valid
        # ===============
        now = datetime.datetime.now()
        cancelled = False
        if user and user.period_end:
            if user.period_end <= now:
                user.paid = False
                user.put()
            else:
                cancelled = True

        if user:
            paying = user.paying
            logging.error("<<<<<<<<<<<<<<< CEHCK USER PAID >>>>>>>>>>>>")
            logging.error("paying: %s" % paying)
            if user.paid:
                paid = True
            else:
                paid = False

        self.render_json({
            "message": "success",
            "paid": paid,
            "paying": paying,
            "cancelled": cancelled
            })

class APIGetUserProfile(MainHandler):
    def get(self, userID):
        if userID:
            user = model.User.get_by_id(int(userID))

            name = user.name
            email = user.email
            fname = user.fname
            lname = user.lname
            postal_code = user.postal_code
            province = user.province

            paid = user.paid

            # ===============
            # Check if user is still valid
            # ===============
            now = datetime.datetime.now()
            cancelled = False
            if user and user.period_end:
                if user.period_end <= now:
                    user.paid = False
                    user.put()
                else:
                    cancelled = True

            next_bill = None
            if user.stripeCustomer:
                subscription_end = json.loads(json.dumps(user.stripeCustomer))["subscriptions"]["data"][0]["current_period_end"]
                subscription_end = datetime.datetime.fromtimestamp(subscription_end)
                next_bill = subscription_end.strftime("%d/%m/%y")

            self.render_json({
                "message": "success",
                "name": name,
                "email": email,
                "fname": fname,
                "lname": lname,
                "postal_code": postal_code,
                "province": province,
                "paid": paid,
                "cancelled": cancelled,
                "next_bill": next_bill
                })
        else:
            self.render_json({
                "message": "fail",
                "long_message": "no userID"
                })

class APISaveUserProfile(MainHandler):
    def post(self, userID):
        if userID:
            user = model.User.get_by_id(int(userID))

            password = self.request.get("password")
            
            postal_code = self.request.get("postalCode")
            name = self.request.get("name")
            newEmail = self.request.get("newEmail")
            newPassword = self.request.get("newPassword")
            verifyPassword = self.request.get("verifyPassword")
            editType = self.request.get("editType")

            logging.error("............ editing user profile")
            logging.error(editType)
            logging.error(password)
            logging.error(postal_code)
            # logging.error(user)

            # =====================
            # Ensure there is a user and that password is confirmed
            # =====================
            if user and utils.confirm_password(user, password):
                
                logging.error("inside the editType area...........")

                if editType == "name":
                    user.name = name
                    user.put()
                    self.render_json({
                        "message": "fail",
                        "invalidName": False,
                        "invalidEmail": False,
                        "invalidPassword": False,
                        "invalidPostalCode": False,
                        "message": "",
                        "userID": userID,
                        "name": name
                    })

                # =====================
                # if email is being changed
                # =====================
                if editType == "email":

                    existing_email = model.User.query(model.User.email == newEmail).get()

                    if not existing_email:
                        new_pw_hash = utils.make_pw_hash(newEmail, password)
                        user.pw_hash = new_pw_hash
                        user.email = newEmail
                        user.put()
                        self.render_json({
                            "invalidName": False,
                            "invalidEmail": False,
                            "invalidPassword": False,
                            "invalidPostalCode": False,
                            "message": "",
                            "userID": userID,
                            "newEmail": newEmail
                        })
                    else:
                        message = "Sorry, that email is already registered."
                        self.render_json({
                            "invalidName": False,
                            "invalidEmail": True,
                            "invalidPassword": False,
                            "invalidPostalCode": False,
                            "message": message,
                            "userID": userID,
                            "newEmail": newEmail
                        })

                # =====================
                # if password is being changed
                # =====================
                if editType == "password":
                    if utils.valid_password(newPassword) and newPassword == verifyPassword:
                        logging.error("OLD HASH %s" % user.pw_hash)
                        new_pw_hash = utils.make_pw_hash(user.email, newPassword)
                        logging.error("NEW HASH %s" % new_pw_hash)
                        logging.error(verifyPassword)
                        user.pw_hash = new_pw_hash
                        user.put()
                        self.render_json({
                            "message": "",
                            "invalidName": False,
                            "invalidEmail": False,
                            "invalidPassword": False,
                            "invalidPostalCode": False,
                            "userID": userID,
                        })
                    else:
                        message = "something went wrong, please try again later"
                        if not utils.valid_password(newPassword):
                            message = "Your password needs to be between 3 and 20 characters long"
                        if newPassword != verifyPassword:
                            message = "Your passwords need to match"
                        if newPassword != verifyPassword and not utils.valid_password(newPassword):
                            message = "Your passwords need to match and be between 3 and 20 characters long"

                        self.render_json({
                            "invalidName": False,
                            "invalidEmail": False,
                            "invalidPassword": True,
                            "invalidPostalCode": False,
                            "message": message,
                            "userID": userID
                        })

                # =====================
                # if postal code is being changed
                # =====================
                if editType == "postal_code":
                    logging.error("POSTAL CODES.....")
                    logging.error(postal_code)
                    province = ""
                    postal_code_obj = model.PostalCode.query(model.PostalCode.postal_code == postal_code).get()
                    logging.error(postal_code_obj)
                    if not postal_code_obj:
                        self.render_json({
                            "invalidName": False,
                            "invalidEmail": False,
                            "invalidPassword": False,
                            "invalidPostalCode": True,
                            "message": "Please include a valid postal code",
                            "userID": userID,
                            "postal_code": postal_code
                        })
                    else:
                        province = utils.province_from_code(postal_code)
                        user.postal_code = postal_code
                        user.province = province
                        user.put()
                        self.render_json({
                            "invalidName": False,
                            "invalidEmail": False,
                            "invalidPassword": False,
                            "invalidPostalCode": False,
                            "message": "",
                            "userID": userID,
                            "postal_code": postal_code
                        })


                # user.name = name
                # existing_user_with_email = model.User.query(model.User.email == email).get()
                # if not existing_user_with_email:
                #     # send confirmation email here
                #     # utils.send_mandrill_mail(subject, html, text, to_email)
                #     user.email = email

                # user.put()

            # self.render_json({
            #     "message": "success",
            #     "name": name,
            #     "email": email,
            #     "postal_code": postal_code,
            #     })

            else:

                self.render_json({
                    "invalidName": False,
                    "invalidEmail": False,
                    "invalidPassword": True,
                    "invalidPostalCode": False,
                    "message": "Invalid password"
                })

        else:

            self.render_json({
                "invalidName": False,
                "invalidEmail": False,
                "invalidPassword": True,
                "invalidPostalCode": False,
                "message": "Invalid password"
            })

class APIGetRegions(MainHandler):
    def get(self):
        regions = model.Region.query().order(model.Region.region).fetch()

        region_list = []

        for r in regions:
            region_obj = {}
            region_obj["id"] = r.key.id()
            region_obj["region"] = r.region

            region_list.append(region_obj)

        self.render_json({
            "regions": region_list
            })

class APIGetLocations(MainHandler):
    def get(self):
        locations = model.Location.query().order(model.Location.city).fetch()

        location_list = []

        for l in locations:
            location_obj = {}
            location_obj["id"] = l.key.id()
            location_obj["city"] = l.city
            location_obj["province"] = l.province
            location_obj["suburb"] = l.suburb

            location_list.append(location_obj)

        self.render_json({
            "locations": location_list
            })

class APIStripePayment(MainHandler):
    def get(self):
        userID = self.request.get("userID")
        user_obj = model.User.get_by_id(int(userID))

        subscription_valid = False
        subscription_end = False
        trial_end = ''
        if user_obj:
            if user_obj.stripeCustomer:
                subscription_end = json.loads(json.dumps(user_obj.stripeCustomer))["subscriptions"]["data"][0]["current_period_end"]
                now = datetime.datetime.now()
                subscription_end = datetime.datetime.fromtimestamp(subscription_end)

                logging.error("NOW: %s" % now)
                logging.error("subscription_end: %s" % subscription_end)

                if subscription_end > now:
                    subscription_valid = True
                    trial_end = subscription_end.strftime("%d/%m/%y")

        self.render("pay-stripe.html", userID=userID, user_obj=user_obj, subscription_end=subscription_end, subscription_valid=subscription_valid, trial_end=trial_end)

    def post(self):
        stripeToken = self.request.get("stripeToken")
        userID = self.request.get("userID")
        coupon = self.request.get("coupon")

        from_web = self.request.get("from_web")

        logging.error("....................................")
        logging.error("stripeToken: %s" % stripeToken)
        logging.error("userID: %s" % userID)
        logging.error("coupon: %s" % coupon)
        user = None
        user_json = None
        if userID:
            user = model.User.get_by_id(int(userID))
            if stripeToken:
                # Set your secret key: remember to change this to your live secret key in production
                # See your keys here https://dashboard.stripe.com/account/apikeys
                stripe.api_key = utils.stripe_api_key
                
                user.stripeToken = stripeToken
                #user.put()# added .put() later

                existing_plan = model.SubscriptionPlan.query().get()

                subscription_plan_name = 'TGH Recruitment Plan'
                subscription_plan_id = 'tghr_basic'

                if not existing_plan:
                    # double check that plan doesn't exist
                    try:
                        created_plan = stripe.Plan.retrieve(subscription_plan_id)
                        if created_plan and not existing_plan:
                            existing_plan = model.SubscriptionPlan().put()
                    except Exception as e:
                        logging.error("something went wrong checking if Stripe subscription plan exists")
                        logging.exception(e)
                        try:
                            #==================================
                            #  create stripe subscription plan
                            # =================================
                            stripe.Plan.create(
                              amount=31500,
                              interval='month',
                              name=subscription_plan_name,
                              currency='zar',
                              id=subscription_plan_id)
                            existing_plan = model.SubscriptionPlan().put()
                        except:
                            logging.error("something went wrong trying to create a Stripe subscription plan")

                    if not created_plan:
                        try:
                            #==================================
                            #  create stripe subscription plan
                            # =================================
                            stripe.Plan.create(
                              amount=31500,
                              interval='month',
                              name=subscription_plan_name,
                              currency='zar',
                              id=subscription_plan_id)
                            existing_plan = model.SubscriptionPlan().put()
                        except:
                            logging.error("something went wrong trying to create a Stripe subscription plan")

                #==================================
                #  associate subscription plan with a customer
                # =================================

                # Get the credit card details submitted by the form
                token = stripeToken# request.POST['stripeToken']

                if not coupon:
                    coupon = None
                # Create a Customer
                customer = stripe.Customer.create(
                  source=token,
                  plan=subscription_plan_id,
                  email=user.email,
                  coupon=coupon
                )

                try:
                    card_id = customer.cards.data[0].id
                    user.stripeCardID = card_id
                    logging.error("----------------got card id")
                except:
                    logging.error("----------------error getting card id")

                user.stripeCustomer = customer
                user.stripeCustomerID = customer.id
                user.paid = True
                user.paying = False
                user.date_paid = datetime.datetime.now()
                user.period_end = None
                user.put()

                # SEND RECEIPT EMAIL HERE.....
                # ........ sending receipt emails from webhook
                # sneding subscription confirmation via webhook after getting the customer.subscription.created event
                # utils.send_mandrill_mail("subscribed", user.email)

                utils.update_counter("clients")

                logging.info("Customer created")
                logging.info(customer)

                user_json = {
                    "userID": user.key.id(),
                    "userEmail": user.email,
                    "paid": True

                }


        # self.response.set_status(200)

        if from_web == "yes":
            self.render("pay-success.html")
        else:
            if user_json:
                self.render_json({
                    "message": "success",
                    "userID": userID,
                    "user": user_json
                    })
            else:
                self.render_json({
                    "message": "success",
                    "userID": userID,
                    "user": user
                    })

class APIStripeUpdatePayment(MainHandler):
    def get(self):
        userID = self.request.get("userID")
        user_obj = model.User.get_by_id(int(userID))
        if user_obj:
            if user_obj.stripeCustomer:
                subscription_end = json.loads(json.dumps(user_obj.stripeCustomer))["subscriptions"]["data"][0]["current_period_end"]
                now = datetime.datetime.now()
                subscription_end = datetime.datetime.fromtimestamp(subscription_end)

                logging.error("NOW: %s" % now)
                logging.error("subscription_end: %s" % subscription_end)

                if subscription_end > now:
                    subscription_valid = True
                    trial_end = subscription_end.strftime("%d/%m/%y")

        self.render("pay-stripe.html", userID=userID, user_obj=user_obj, update=True)

    def post(self):
        stripe.api_key = utils.stripe_api_key

        userID = self.request.get("userID")
        stripeToken = self.request.get("stripeToken")
        from_web = self.request.get("from_web")

        user_obj = model.User.get_by_id(int(userID))

        # retrieve customer
        customer = stripe.Customer.retrieve(user_obj.stripeCustomerID)
        #add a new card
        logging.error("stripeToken")
        logging.error(stripeToken)
        card = customer.sources.create(source=stripeToken)
        #delete old card
        customer.sources.retrieve(user_obj.stripeCardID).delete()
        
        logging.error("Some stuff to see")
        logging.error("old card id %s" % user_obj.stripeCustomerID)
        logging.error("new card id %s" % card.id)

        #update user on our DB
        user_obj.stripeCardID = card.id
        user_obj.stripeToken = stripeToken
        user_obj.stripeCustomer = customer
        user_obj.period_end = None
        user_obj.put()

        if from_web == "yes":
            self.render("pay-success.html")
        else:
            if user_json:
                self.render_json({
                    "message": "success",
                    "userID": userID,
                    "user": user_json
                    })
            else:
                self.render_json({
                    "message": "success",
                    "userID": userID,
                    "user": user
                    })



class APIUserPaying(MainHandler):
    def post(self):
        userID = self.request.get("userID")
        paying = self.request.get("paying")

        logging.error("<<<<<<<<<<<<<<< SET USER PAYING >>>>>>>>>>>>")
        logging.error("paying: %s" % paying)
        logging.error("userID: %s" % userID)

        if userID:
            user = model.User.get_by_id(int(userID))
            if user:
                if paying:
                    if paying == "yes":
                        logging.error("<<<<<<<<<<<<<<< YES... now paying >>>>>>>>>>>>")
                        user.paying = True
                    elif paying == "no":
                        user.paying = False
                    else:
                        user.paying = True

                else:
                    user.paying = True
                
                user.put()

                logging.error("DID IT STICK?...... %s" % user.paying)

                self.render_json({
                    "message": "success",
                    "user_paying": True
                    })
            else:
                self.render_json({
                    "message": "success",
                    "user_paying": False
                    })
        else:
            self.render_json({
                "message": "success",
                "user_paying": False
                })



# ======================
#  Tests & tasks
# ======================

class TaskTest(MainHandler):
    def get(self):
        # taskqueue.add(url='/worker', params={'key': key})
        # taskqueue.add(url='/test')
        taskqueue.add(url='/postal_code')

        self.response.out.write("task started... I think")

class UndoTaskTest(MainHandler):
    def get(self):
        # taskqueue.add(url='/worker', params={'key': key})
        taskqueue.add(url='/undotest')

        self.response.out.write("task undoing... I think")

class Test(MainHandler):
    def post(self):
        path = os.path.join(os.path.split(__file__)[0], 'barmen-data.csv')
        content = open(path, 'r').read() 

        reader = csv.reader(content.split('\n'), delimiter=',')

        position = 'barman'

        cities = []
        suburbs = []
        regions = []

        for row in reader:
            if len(row) >= 3:
                name = row[0].decode('ascii', 'ignore')
                contact = row[1].decode('ascii', 'ignore')# not made lower case since emails may be case sensitive
                skills = row[2].split(',')
                for index, item in enumerate(skills):
                    if item.strip().lower() == 'sab draught':
                        item = 'draught'
                    if item.strip().lower() == 'cocktails':
                        item = 'cocktail'
                    skills[index] = item.lower()


                bartender = False
                waitress = False
                host = False
                draught = False
                cocktail = False
                wine = False
                spirits = False
                coffee = False

                for skill in skills:
                    logging.error("--------------------- SKILL %s " % skill)
                    if skill.strip() == 'bartender':
                        bartender = True

                    if skill.strip() == 'waitress':
                        waitress = True

                    if skill.strip() == 'host':
                        host = True

                    if skill.strip() == 'sab draught':
                        draught = True

                    if skill.strip() == 'cocktails':
                        cocktail = True
                    elif skill.strip() == 'cocktail':
                        cocktail = True

                    if skill.strip() == 'wine':
                        wine = True

                    if skill.strip() == 'spirits':
                        spirits = True

                    if skill.strip() == 'coffee':
                        coffee = True


                    # waitress = True if skill == 'waitress' else waitress = False
                    # host = True if skill == 'host' else host = False
                    # draught = True if skill == 'draught' else draught = False
                    # cocktail = True if skill == 'cocktail' else cocktail = False
                    # wine = True if skill == 'wine' else wine = False
                    # spirits = True if skill == 'spirits' else spirits = False
                    # coffee = True if skill == 'coffee' else coffee = False

                suburb = row[3].decode('ascii', 'ignore')

                if suburb not in suburbs:
                    if suburb != "Suburb":
                        suburbs.append(suburb)

                city = row[4].decode('ascii', 'ignore')

                if city not in cities:
                    if city != "City":
                        cities.append(city)

                region = row[5].decode('ascii', 'ignore')

                if region not in regions:
                    if region != "Region":
                        regions.append(region)

                # position = row[-1].decode('ascii', 'ignore')
                # if len(row) > 3:
                #     skills = row[2].split(',')
                # else:
                #     skills = []

                if len(name) > 0 and len(contact) > 0:
                    b = model.Employee( 
                        name=name.lower(), 
                        email_contact=contact, 
                        position=position.lower(), 
                        skills=skills, 
                        suburb=suburb.lower(), 
                        city=city.lower(), 
                        region=region.lower(),
                        bartender = bartender,
                        waitress = waitress,
                        host = host,
                        draught = draught,
                        cocktail = cocktail,
                        wine = wine,
                        spirits = spirits,
                        coffee = coffee,
                         )
                    b.put()

        for s in suburbs:
            su = model.Suburb(suburb=s)
            su.put()

        for c in cities:
            ci = model.City(city=c)
            ci.put()

        for r in regions:
            re = model.Region(region=r)
            re.put()
        
        logging.error("................. TASK DONE")

        # self.response.out.write( "Done" )
        
            # print '\t'.join(row)

        # with open(path, 'rb') as csvfile:
        #     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        # for row in spamreader:
        #     self.response.out.write( "%s <br>_________________________<br>" % row )

        # csvreader = csv.reader(path, delimiter=',')
        # for row in csvreader:
        #     self.response.out.write( "%s <br>_________________________<br>" % row )

        # self.response.out.write(content)

class UndoTest(MainHandler):
    def post(self):

        # employees = model.Employee.query().fetch()

        # suburbs = model.Suburb.query().fetch()
        # cities = model.City.query().fetch()
        # regions = model.Region.query().fetch()

        # for e in employees:
        #     e.key.delete()

        # for s in suburbs:
        #     s.key.delete()

        # for c in cities:
        #     c.key.delete()

        # for r in regions:
        #     r.key.delete()

        postal_codes = model.PostalCode.query().fetch()

        for p in postal_codes:
            p.key.delete()

        # self.response.out.write("un-done")
        logging.error("Task Undone.....................")

class TaskPopulateSkills(MainHandler):
    def get(self):
        taskqueue.add(url='/taskpopulateskillsFN')
        self.response.out.write("populating total skills")

class TaskPopulateSkillsFN(MainHandler):
    def post(self):
        employees = model.CapturedEmployee.query().fetch()

        for e in employees:
            total_skills = 0
            if e.coffee:
                total_skills += 1
            if e.wine:
                total_skills += 1
            if e.front_manage:
                total_skills += 1
            if e.cocktail:
                total_skills += 1
            if e.silver:
                total_skills += 1
            if e.scullery:
                total_skills += 1
            if e.cook:
                total_skills += 1
            if e.back_manage:
                total_skills += 1
            if e.food_manage:
                total_skills += 1

            e.total_skills = total_skills
            e.put()

class TaskPopulateArea(MainHandler):
    def get(self):
        taskqueue.add(url='/taskpopulateareaFN')
        self.response.out.write("populating area/suburb")

class TaskPopulateAreaFN(MainHandler):
    def post(self):
        employees = model.CapturedEmployee.query().fetch()

        for e in employees:
            if e.postal_code:
                area = utils.area_suburb_from_code(e.postal_code)[0]
                suburb = utils.area_suburb_from_code(e.postal_code)[1]

                # if post_code_obj:
                e.suburb = suburb
                e.area = area
                e.put()





class CheckCustomer(MainHandler):
    def get(self):
        email = self.request.get("email")

        user = model.User.query(model.User.email == email).get()
        if user:
            self.render_json(user.stripeCustomer)
        else:
            self.render_json({"message": "no user"})

class PostalCode(MainHandler):
    def post(self):
        path = os.path.join(os.path.split(__file__)[0], 'postcode-data.csv')
        content = open(path, 'r').read() 
        reader = csv.reader(content.split('\n'), delimiter=',')
        post_code_locations = []
        postal_codes_tracking = []
        count = 0
        def pad_zero(string):
            return string.zfill(4)
        for row in reader:
            count += 1
            if count > 1:
                post_obj = {}
                post_obj["streetpostcode"] = None
                post_obj["boxpostcode"] = None
                if len(row[3]) > 0:
                    postal_code = post_obj["postcode"] = pad_zero( row[3] )
                    postal_code = "".join(postal_code.split())
                elif len(row[2]) > 0:
                    postal_code = post_obj["postcode"] = pad_zero( row[2] )
                if not postal_code in postal_codes_tracking:
                    post_obj["suburb"] = row[1].lower()
                    post_obj["area"] = row[4].lower()
                    if row[3]:
                        post_obj["streetpostcode"] = pad_zero( row[3] )
                    if row[2]:
                        post_obj["boxpostcode"] = pad_zero( row[2] )
                    postal_codes_tracking.append(postal_code)
                    post_code_locations.append(post_obj)
                    pc = model.PostalCode( 
                        area=post_obj["area"], 
                        suburb=post_obj["suburb"], 
                        postal_code=post_obj["postcode"], 
                        box_postal_code=post_obj["boxpostcode"],
                        street_postal_code=post_obj["streetpostcode"] )
                    pc.put()

class GoogleSiteVerification(MainHandler):
    def get(self):
        self.render("google614754be65f762b3.html")
    def post(self):
        self.render("google614754be65f762b3.html")

class SlotMachine(MainHandler):
    def get(self):
        self.render("/slots/slots.html")

class EmailTest(MainHandler):
    def get(self):

        email = "emile.esterhuizen@gmail.com"
        new_pw = "1234"

        #sends email and returns html
        html = emails.render_and_send_email_template("forgot_password", email, name="Emile", new_pw=new_pw)

        # email_obj = {
        #     "html": html,
        #     "text": "Hi,\r\n We have received a request to have your password reset for PubHub. If you did not request this then please ignore this email.\r\n To reset your password please log in with the below and then choose a new password from your settings:\r\n %s,\r\n\r\n Pubhub Team" % new_pw,
        #     "subject": "Pubhub - forgotten password"
        # }
        #utils.send_mandrill_mail_template(email_obj, email)

        self.response.out.write(html)

app = webapp2.WSGIApplication([
    # site verification
    ('/google614754be65f762b3.html', GoogleSiteVerification),

    # General
    ('/', Home),
    #('/slot_machine', SlotMachine),

    # Admin
    ('/admin', Admin),
    ('/admin/locations', AdminLocations),
    ('/admin/clients', AdminClients),
    ('/admin/client/(\w+)', AdminClient),
    ('/admin/employees', AdminEmployees),
    ('/admin/employees/csv', AdminEmployeesCSV),
    ('/admin/employee/(\w+)', AdminEmployee),
    ('/admin/employee/delete/(\w+)', AdminEmployeeDelete),

    # Employee data capture
    ('/check_postal_code', CheckPostalCode),
    ('/employees/confirm', EmployeeConfirmRedirect),
    ('/employees/\w+/confirm', EmployeeConfirmRedirect),
    ('/pubhub/confirm', EmployeeConfirm),
    ('/confirm', EmployeeConfirm),
    ('/employee/thank_you', EmployeeThankYou),
    ('/employee/refer/email', EmployeeReferEmail),

    # Desktop API
    ('/login', Login),
    ('/logout', Logout),
    ('/user/profile', UserProfile),

    # Mobile API
    ('/api/register', APIRegister),
    ('/api/login', APILogin),
    ('/api/forgot_password', APIForgotPassword),
    ('/api/candidate', APICandidate),
    ('/api/set_user_paying', APIUserPaying),
    ('/api/user_paid', APIUserPaid),
    ('/api/profile/(\w+)', APIGetUserProfile),
    ('/api/profile/save/(\w+)', APISaveUserProfile),
    ('/api/get_regions', APIGetRegions),
    ('/api/get_locations', APIGetLocations),
    #mobile payments with Stripe
    ('/api/stripe_payment', APIStripePayment),
    ('/api/cancel_subscription', APICancelStripeSubscription),
    ('/api/get_stripe_publishable_key', APIGetStripePublishableKey),

    # Payments
    ('/staging/get-token', GetToken),
    ('/staging/check-used-token', CheckUsedToken),
    ('/staging/pay-test', PayTest),
    ('/staging/pay-test-notify', PayTestNotify),
    ('/staging/pay-test-success', PayTestSuccess),
    ('/staging/pay-test-cancel', PayTestCancel),

    #stripe payments
    ('/stripe/check_coupon/(\w+)', StripeCheckCoupon),
    # ('/pay_stripe', PayStripe),
    ('/pay_stripe', APIStripePayment),# testing out using the mobile payment class
    ('/update_payment', APIStripeUpdatePayment),# testing out using the mobile payment class
    ('/cancel_stripe_subscription', APICancelStripeSubscription),
    ('/cancel_stripe_payment', CancelStripePayment),
    ('/stripe/webhook', StripeWebhook),

    # tests
    ('/tasktest', TaskTest),
    ('/undotasktest', UndoTaskTest),
    ('/test', Test),
    ('/undotest', UndoTest),
    ('/email_test', EmailTest),

    #populate total skills
    # ('/taskpopulateskills', TaskPopulateSkills),
    # ('/taskpopulateskillsFN', TaskPopulateSkillsFN),

    #populate area and suburb based on postal code
    # ('/taskpopulatearea', TaskPopulateArea),
    # ('/taskpopulateareaFN', TaskPopulateAreaFN),

    ('/check_customer', CheckCustomer),
    ('/postal_code', PostalCode)

], debug=False)
