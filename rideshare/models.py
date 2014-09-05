from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import rideshare.settings
import string
import random

class Ride(models.Model):
    owner = models.ForeignKeyField(User)
    driver = models.ForeignKeyField(User,blank=True,null=True)
    passengers = models.ManyToManyField(User)
    leave_time_start = models.DateTimeField()
    leave_time_end = models.DateTimeField()
    start = models.ForeignKeyField(Location)
    end = models.ForeignKeyField(Location)
    max_passengers = models.PositiveIntegerField(default=1)

class Comment(models.Model):
    author = models.ForeignKeyField(User)
    body = models.TextField()
    ride = models.ForeignKeyField(Ride)

class Location(models.Model):
    state = models.ForeignKeyField(State)
    city = models.CharField(max_length=64)
    address = models.CharField(max_length=256)

class State(models.Model):
    name = models.CharField(max_length=64)

class User(AbstractBaseUser):
    name = models.CharField(max_length=256)
    phone_number = models.CharField(max_length=16)
    email = models.CharField(max_length=256)
    verified = models.BooleanField(default=False)
    class_year = models.PositiveIntegerField(blank=True,null=True)
    USERNAME_FIELD = 'email'
    def generate_token(self):
        ja = AuthToken(user=self, auth_code=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20)))
        ja.save()
        return ja


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, pwd=None):
        js = User(email=email, name=first_name + last_name)
        if pwd: js.set_password(pwd)
        js.save()
        return js

    def create_superuser(self, email, first_name, last_name, pwd):
        return self.create_user(email, first_name, last_name, pwd=pwd)

    def get_by_natural_key(self, email):
        return self.get(email=email)

class AuthToken(models.Model):
    auth_code = models.CharField(max_length=64)
    user = models.ForeignKeyField(User)
