#-*- coding: utf-8 -*- 
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
import urllib
import urllib2
import httplib
import hashlib
import datetime
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson as json_simple
import logging, random, hashlib, string
import dbmerge, os
from Crypto.Cipher import DES
import pymongo
from pymongo import Connection
import dbdecrypt
import decrypt
import sqlite3
import shutil
import time
from bson import json_util
import json, ast
import sys
import settings
from django.template import RequestContext
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.utils.http import urlencode
from oauth2app.authenticate import Authenticator, AuthenticationException, JSONAuthenticator
import requests
from oauth2app.models import AccessRange, AccessToken
import apps.oauth2
from django.contrib.auth.decorators import login_required

import pdb
import traceback

upload_dir = settings.SERVER_UPLOAD_DIR

def insert_pds(profile, token, pds_json):
    try:
	#print "Attempting to post to PDS"
        # get pds location and user id
	request_path= "http://"+str(profile.pds_location)+"/api/personal_data/funf/?format=json&bearer_token="+str(token)+"&datastore_owner__uuid="+str(profile.uuid)
	payload = json.dumps(pds_json)
	r = requests.post(request_path, data=payload, headers= { "content-type": "application/json" })
	response = r.text
	#print "PDS POST response:"
	#print response
    except Exception as ex:
	#print ex
	raise Exception(ex)
    return response

def write_key(request):
    '''write the password used to encrypt funf database files to your PDS'''
    response = None
    try:
        token = request.GET['bearer_token']
        scope = "funf_write"
        scope = AccessRange.objects.get(key="funf_write")
        authenticator = Authenticator(scope=scope)
        try:
            # Validate the request.
            authenticator.validate(request)
        except AuthenticationException:
            # Return an error response.
            return authenticator.error_response(content="You didn't authenticate.")
        profile = authenticator.user.get_profile()
        profile.funf_password = json.loads(request.raw_post_data)['key']
        profile.save()
        response_content = json.dumps({'status':'success'})
        response = HttpResponse(content=response_content)        
    except Exception as ex:
        print "EXCEPTION:"
        print ex
        response = HttpResponseBadRequest('failed to write funf key')
    return response
 

def data(request):
    '''decrypt funf database files, and upload them to your PDS'''
    result = {}
    connection = None
    token = request.GET['bearer_token']

    if request.method == 'GET':
        template = {'token': token}
        return render_to_response('upload.html', template, RequestContext(request))
    pds = None
    scope = AccessRange.objects.get(key="funf_write")
    authenticator = JSONAuthenticator(scope=scope)
    try:
        # Validate the request.
        authenticator.validate(request)
    except AuthenticationException as e:
        # Return an error response.
        print e
        return authenticator.error_response(content="You didn't authenticate.")
    profile = authenticator.user.get_profile()
    funf_password = profile.funf_password
    print "Registry set_funf_data for uuid: %s" % profile.uuid

    for filename, file in request.FILES.items():
        try:
            file_path = upload_dir + file.name
            try:
                key = decrypt.key_from_password(str(funf_password))
                write_file(str(file_path), file)
            except Exception as ex:
                print "failed to write file to "+file_path+".  Please make sure you have write permission to the directory set in settings.SERVER_UPLOAD_DIR"
            dbdecrypt.decrypt_if_not_db_file(file_path, key)
            con = sqlite3.connect(file_path)
            cur = con.cursor()
            cur.execute("select name, value from data")
            inserted = []
            for row in cur:
                name = convert_string(row[0])
                json_insert = clean_keys(json.JSONDecoder().decode(convert_string(row[1])))
                #print json_insert
                # Insert into PDS
                pds_data= {}
                pds_data['time']=json_insert.get('timestamp')
                pds_data['value']=json_insert
                pds_data['key']=name
                insert_pds(profile, token, pds_data)
                #print "inserting row..."
                #print pds_data
                inserted.append(convert_string(json_insert)+'\n')
            result = {'success': True, 'message':''.join(inserted)} 
            #remove_file(file_path)
        except Exception as e:
            print e.message
            print traceback.format_exc()
            result = {'success':False, 'error_message':e.message}
    # It doesn't matter what we return at this point - the phones are just checking the response status
    response_dict = {"status":"success"}
    return HttpResponse(json.dumps(response_dict), content_type='application/json')


TMP_FILE_SALT = '2l;3edF34t34$#%2fruigduy23@%^thfud234!FG%@#620k'
TEMP_DATA_LOCATION = "/data/temp/"

def random_hash(pk):
    randstring = "".join([random.choice(string.letters) for x in xrange(20)])
    hash = hashlib.sha224(TMP_FILE_SALT + pk + randstring).hexdigest()[0:40]
    return hash

    
def direct_decrypt(file, key, extension=None):
    assert key != None
    decryptor = DES.new(key) #TODO to make sure the key is 8 bytes long. DES won't accept a shorter key
    encrypted_data = file.read()
    data = decryptor.decrypt(encrypted_data)
    return data


def write_file(filename, file):
    if not os.path.exists(upload_dir):
        os.mkdir(upload_dir)
    filepath = os.path.join(upload_dir, filename)
    if os.path.exists(filepath):
        backup_file(filepath)
    with open(filepath, 'wb') as output_file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            output_file.write(chunk)

def remove_file(filename):
    filepath = os.path.join(upload_dir, filename)
    print "filepath: %s" % filepath
    if os.path.exists(filepath):
        print "... exists!"
        os.remove(filepath)

def backup_file(filepath):
    shutil.move(filepath, filepath + '.' + str(int(time.time()*1000)) + '.bak')


def convert_string(s):
    return "%s" % s

def clean_keys(d):
    '''replace all "." with "-" and force keys to lowercase'''
    new = {}
    for k, v in d.iteritems():
        if isinstance(v, dict):
            v = clean_keys(v)
	if isinstance(v, list):
	    for idx,i in enumerate(v):
		if isinstance(i, dict):
       		    v[idx] = clean_keys(i)	
        new[k.replace('.', '-').lower()] = v
    return new


