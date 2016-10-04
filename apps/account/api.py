from django.contrib.auth.models import User
from apps.account.models import Profile, Group
from tastypie import fields
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import BadRequest
from django.db import IntegrityError
from oauth2app.models import Client, AccessRange
import pdb
import logging

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        authorization = Authorization()
        excludes = ['last_login', 'password', 'date_joined']
 
    def obj_create(self, bundle, request=None, **kwargs):
        username, password = bundle.data['username'], bundle.data['password']
        try: 
            logging.debug("Creating User")
            bundle.obj = User.objects.create_user(username, '', password)
            logging.debug("User Created")
        except IntegrityError as e:
            logging.debug("INTEGRITY ERROR")
            logging.debug("Integrity Error: %s - %s" % (str(e.errno), e.strerror))
            raise BadRequest('That username already exists.')
        return bundle

class GroupResource(ModelResource):
    class Meta:
        queryset = Group.objects.all()
        authorization = Authorization()
#	excludes = ['is_staff', 'is_superuser', 'last_login', 'password', 'date_joined']

class ClientResource(ModelResource):
    class Meta:
        queryset = Client.objects.all()
        authorization = Authorization()
#	excludes = ['is_staff', 'is_superuser', 'last_login', 'password', 'date_joined']

class ScopeResource(ModelResource):
    class Meta:
        queryset = AccessRange.objects.all()
        authorization = Authorization()
#	excludes = ['is_staff', 'is_superuser', 'last_login', 'password', 'date_joined']

class ProfileResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user', full=True)
#    group = fields.ForeignKey(GroupResource, 'group', full=True, null=True, blank=True)
#    client = fields.ForeignKey(ClientResource, 'client', full=True, null=True, blank=True)

    class Meta:
        queryset = Profile.objects.all()
        authorization = Authorization()
#	excludes = ['is_staff', 'is_superuser', 'last_login', 'password', 'date_joined']
   
    def obj_create(self, bundle, request=None, **kwargs): 
        try:
            password = bundle.data["user"].pop("password")
            logging.debug("PASSWORD: %s" % password)
            bundle = super(ProfileResource, self).obj_create(bundle, request, **kwargs)
            logging.debug("Profile Created")
            bundle.obj.user.set_password(password)
            logging.debug("User Password Set")
            bundle.obj.user.save()
        except IntegrityError as e:
            logging.debug("INTEGRITY ERROR")
            logging.debug("Integrity Error: %s " % (e.message))
            raise BadRequest('Username already exists')
        return bundle

