from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import string
import random

class State(models.Model):
    name = models.CharField(max_length=64)

class Location(models.Model):
    state = models.ForeignKey(State)
    city = models.CharField(max_length=64)
    address = models.CharField(max_length=256)

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

class User(AbstractBaseUser):
    name = models.CharField(max_length=256)
    phone_number = models.CharField(max_length=16)
    email = models.CharField(max_length=256,unique=True)
    verified = models.BooleanField(default=False)
    class_year = models.PositiveIntegerField(blank=True,null=True)
    USERNAME_FIELD = 'email'
    objects = UserManager()
    def generate_token(self):
        ja = AuthToken(user=self, auth_code=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20)))
        ja.save()
        return ja
    def to_dict(self):
        return { 'name': self.name, 'phone_number': self.phone_number, 'email': self.email,
            'verified': self.verified, 'id': self.id, 'class_year': self.class_year }

class Ride(models.Model):
    owner = models.ForeignKey(User, related_name='rides_created')
    driver = models.ForeignKey(User,blank=True,null=True,related_name='rides_driven')
    passengers = models.ManyToManyField(User,related_name='rides_taken')
    leave_time_start = models.DateTimeField()
    leave_time_end = models.DateTimeField()
    start = models.ForeignKey(Location,related_name='rides_from')
    end = models.ForeignKey(Location,related_name='rides_to')
    max_passengers = models.PositiveIntegerField(default=1)

class Comment(models.Model):
    author = models.ForeignKey(User)
    body = models.TextField()
    ride = models.ForeignKey(Ride)

class AuthToken(models.Model):
    auth_code = models.CharField(max_length=64)
    user = models.ForeignKey(User)
