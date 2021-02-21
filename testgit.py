import json
import requests
# from requests.auth import HTTPBasicAuth
import pprint
from collections import defaultdict
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from flask import Flask,render_template,request,flash,redirect


# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
cred = credentials.Certificate('/Users/saravananmano/Downloads/hacksc2021-2fc5f-firebase-adminsdk-db9o5-ad4549d152.json')
default_app = initialize_app(cred)
db = firestore.client()
lang_collection = db.collection('languages')
user_collections = db.collection('users')


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        details = request.form
        username = details['userName']
        language_dict = insert_lang(username)
        firstName = details['firstName']
        lastName = details['lastName']
        email = details['emailID']
        user_url = "https://api.github.com/users/" + username
        image_url = requests.get(user_url).json()["avatar_url"]
        user_collections.document(username).set({
            'first_name':firstName,
            'last_name': lastName,
            'email' : email,
            'image_url' : image_url,
            'languages' : list(language_dict.keys())
        })
        return render_template('signup.html', success="success")
    return render_template('signup.html')

def insert_lang(username):
    try:
        ''' retrives data from Github and populates the Languages collection '''
        lang_doc_struct = {'Intermediate':[],
                'Beginner':[],
                'Expert':[]
        }

        data = requests.get("https://api.github.com/users/" + username + "/repos")
        data = data.json()
        language_dict = {}
        language_level = {}
        for i in data:
            lang_data = requests.get(i["languages_url"])
            languages = lang_data.json()
            for lang in languages:
                print(lang,languages[lang])
                if lang in language_dict.keys():
                    language_dict[lang] += int(languages[lang])
                else:
                    language_dict[lang] = int(languages[lang])

        for i in language_dict:
            if language_dict[i] > 100000:
                language_level[i] = 'Expert'
            elif language_dict[i] < 50000:
                language_level[i] = 'Beginner'
            else:
                language_level[i] = 'Intermediate'
        
        for skill in language_level:
            try:
                lang_collection.document(skill).update({language_level[skill]:firestore.ArrayUnion([username])})
            except:
                lang_collection.document(skill).set(lang_doc_struct)
                lang_collection.document(skill).update({language_level[skill]:firestore.ArrayUnion([username])})
        return language_dict
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/lookup', methods=['GET','POST'])
def lookup():
    if request.method=='POST':
        details = request.form
        query_lang = details['lang']
        query_level = details['level']
        print(query_lang,query_level)
        lang_ref = lang_collection.document(query_lang)
        lang_doc = lang_ref.get()
        user_list = lang_doc.to_dict()[query_level]
        user_information = [] #list of tuple(emailID,first_name,last_name)
        print(user_list)
        for user in user_list:
            user_doc = user_collections.document(user).get().to_dict()
            user_git_url = "https://github.com/" + user
            user_information.append((user_doc['email'],user_doc['first_name'],user_doc['last_name'],user_doc['image_url'],user_git_url,user_doc['languages']))
    
        return render_template("result.html", user_information = user_information)

    return render_template("lookup.html")


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)