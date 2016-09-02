#Leeloo Datahub API
Leeloo provides an API into Datahub for Datahub clients. Using Leeloo you can search for entities
and manage companies, contacts and interactions.

![Leeloo](leeloo.jpg)

## Developer setup

Clone this Git repository and then use virtualenv to create a python environment:

    cd leeloo-api
    virtualenv env --python=python3.5
    source env/bin/activate

Update pip to the latest version:

    pip install -U pip

Install python dependencies:

    pip install -r requirements.txt

## Required servers
Leeloo is designed to use Postgresql as a DB (though in theory you could use sqlite).
Leeloo also requires Elastic Search. These can either be run locally or use a hosted version.
 
 Don't forget to run:
 
     python manage.py migrate

## Environment variables
All config is provided via environment variables.

### Required
* **DATABASE_URL** A DJ Database compatible url for the DB e.g. postgres://user:password@host:5432/dbname
* **ES_HOST** The hostname for your elastic search server e.g. localhost
* **ES_PORT** The port number for Elastic search, e.g. 9200

### Optional
The following environment variables are optional
* **ES_ACCESS** If your Elasctic search server runs on a secure service such as those provided by Amazon, you must
  provide an access id and secret
* **ES_SECRET** The secret to go with your access id
* **ES_REGION** If you are using Amazon Elastic search, you must provide the region in order to authenticate, e.g. eu-west-1

## Tasks
A few management tasks have been added to help 

### drop_index
This command simple drops the index in elastic search and creates a new one. Handy for developers when they are working on scheme changes.

### load_ch
Companies house provide free copies of a sub set of their data in the form of csv files. These can be found via google. Once 
you have them, use load_ch to bulk import them into the DB and elastic search. This is a work in progress and currently only
useful to import CH data before you start development. If you import data and the company number is already in the database 
the record will not be imported.

python manage.ph load_ch /path/to/file.csv

### rebuild_index
This will drop the elastic search index and then rebuilt it's contents based on the contents of the ch_company table
