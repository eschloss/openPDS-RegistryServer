openPDS - Registry Server
======================================

* What is the Registry Server?
 
    The Registry Server is a trustframework registry (includes users, roles etc..) and is also an OAuth 2.0 registry.

* To get started, you'll need python pip and virtualenv installed on your machine (this probably will require root access)

    >apt-get install python-pip
    
    >apt-get install python-virtualenv
    
    >make sure you have the heroku CLI installed

    >virtualenv registryEnv
    
    >cd registryEnv
    
    >source bin/activate
    
    >go to https://github.com/eschloss/openPDS-RegistryServer and fork it
    
    >setup a new heroku app using the forked repository
    
    >git clone {{ URL to your forked github repository }} -b master

    >cd openPDS-RegistryServer
    
    >heroku git:remote -a {{name of your heroku app}}
    
    >pip install -r requirements.txt

    >cd registryServer
    
    >python manage.py syncdb
    
    >python manage.py runserver 0.0.0.0:8000 (for access to local VM)
    
* The above steps will get you started with a registry server on port 8000 of your machine's loopback interface (for local access only).

* Additional steps required for full openpds setup
    
    >change pdsDefaultLocation in settings.py file
    
    >provision a postgres database in the heroku dashboard or CLI
    
    >provision newrelic for monitoring or remove newrelic from the Procfile and requirements.txt
    
* sync the production database
    > heroku run python manage.py syncdb
    
    > choose a superuser username/password when prompted
    
        
    
