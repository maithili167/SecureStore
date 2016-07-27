
"""Cloud Foundry test"""
from flask import Flask,render_template,request,redirect,url_for,session
import os
import swiftclient
import keystoneclient
import MySQLdb
import pyDes
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key='mysecret'

app.config['MAX_CONTENT_LENGTH']= 1024*1024
filesize=1000000
maxfile=10000000


auth_url= "**" + '/v3'
password= "**"
project="**"
projectId= "**"
region= "**"
userId= "**"
username= "**"

def createconn():
    conn = swiftclient.Connection(key=password,
    authurl=auth_url,
    auth_version='3',
    os_options={"project_id": projectId,
    "user_id": userId,
    "region_name": region})
    return conn


# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))


#Root URL which redirects to home page
@app.route('/')
def Welcome():
    return render_template('login.html')

@app.route("/home")
def home():
    return render_template("main.html")

# @app.route('/login')
# def hello_world():
#     return render_template("main.html")

container_name = 'Newcontainer'
def createcontainer():
    # create container
    conn = createconn()
    conn.put_container(container_name)

@app.route("/object",methods=['GET','POST'])
def objectStorage():
    # createcontainer()
    return render_template("obj.html")
#upload file

@app.route('/upload',methods=['GET','POST'])
def Uploadfile():
    conn = createconn()
    totsize=0
    for container in conn.get_account()[1]:
        for data in conn.get_container(container['name'])[1]:
            totsize+=data['bytes']
    print "totsize",totsize
    if totsize <10000000:
        try:
            file=request.files['myfile']
            file_name=file.filename
            data = file.read()
            datalen=len(data)
            print "datalen",datalen
            if datalen<1000000:
                k = pyDes.des("DESCRYPT", pyDes.CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
                d = k.encrypt(data)
                print "beforeupload" + d
                with open(file_name,'w') as example_file:
                    conn.put_object(container_name,
                    file_name,
                    contents=d,
                    content_type='text/plain')
                message = "File uploaded successfully"
            else:
                message = "File size exceeds"
        except:
            return 413
    else:
        message = "Quota limit exceeds"
    return render_template('result.html',message=message)


#To list files
@app.route('/list',methods=['GET','POST'])
def ShowfileList():
    dict_files=[]
    conn = createconn()
    for container in conn.get_account()[1]:
        for data in conn.get_container(container['name'])[1]:
            dict={}
            dict['name']=data['name']
            dict['bytes']=data['bytes']
            dict_files.append(dict)
    return render_template('list.html',result=dict_files)

#To delete files
@app.route('/delete',methods=['GET','POST'])
def DeleteFile():
    conn = createconn()
    file_name=request.args.get('file')
    conn.delete_object(container_name,file_name)
    message = "Selected file has been deleted!"
    return redirect(url_for('ShowfileList'), code=302)

#To download file
@app.route('/download',methods=['GET','POST'])
def DownloadFile():
    conn = createconn()
    file_name=request.args.get('file')
    file_details=conn.get_object(container_name,file_name)
    k = pyDes.des("DESCRYPT", pyDes.CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
    with open(file_name,'w') as my_copy:
    	my_copy.write(k.decrypt(file_details[1]))
        print "bluemix"+file_details[1]
    message= "Selected file has been downloaded!"
    return redirect(url_for('ShowfileList'), code=302)


####################################################################################################

def dbconn():
    db = MySQLdb.connect(host="*****",  # your host, usually localhost
                         user="****",  # your username
                         passwd="****",  # your password
                         db="******")  # name of the data base

    return db


@app.route('/login',methods=['GET','POST'])
def SignIn():
    username=request.form['username']
    password=request.form['password']
    message = "wrong username or password"
# you must create a Cursor object. It will let
#  you execute all the queries you need
    db=dbconn()
    cur=db.cursor()

# Use all the SQL you like
    #cur.execute("SELECT username,user_password FROM app_user where username=%s and user_password=%s;",username,password)
    select_stmt = "SELECT id,username,user_password FROM app_user where username = %(username)s and user_password=%(user_password)s"
    cur.execute(select_stmt, { 'username': username,'user_password':password})

# print all the first cell of all the rows
    for row in cur.fetchall():
        if row[1]==username:
            if row[2]==password:
                message="Welcome " + username + " !!!"
                session['username']=username
                session['id']=row[0]
                db.close()
                return render_template('main.html',message=message)
            else:
                db.close()

                return render_template('login.html',message=message)
        else:
            db.close()
            return render_template('login.html',message=message)
    return render_template('login.html',message=message)

@app.route("/db",methods=['GET','POST'])
def checkdbconn():

    return render_template("dbop.html")

@app.route("/uploaddb",methods=['GET','POST'])
def uploaddb():
    # filesize = compute_size('1')
    # print filesize
    db=dbconn()
    cur=db.cursor()
    filess = request.files['myfile']
    des = request.form['filedes']
    file_name = secure_filename(filess.filename)
    f = open(file_name, "rb", 2048)
    thedata = filess.read()
    fsize = len(thedata)
    uid=session['id']
    # Use all the SQL you like
    # cur.execute("SELECT username,user_password FROM app_user where username=%s and user_password=%s;",username,password)
    #FOR TOTAL SIZE "select sum(fsize) from user_data where user_id=2"
    select_stmt = "select count(*) from user_data where user_id = %(user_id)s and file_description = %(file_description)s"
    cur.execute(select_stmt, {'user_id': uid,'file_description':des})
    for row in cur.fetchall():
        versionnum=row[0]
    versionnum=versionnum+1
    insert_stmt = "Insert into user_data (user_id,file_description,user_file,versionnum,fsize) VALUES (%s,%s,%s,%s,%s)"
    data = (uid, des, thedata,versionnum,fsize)
    cur.execute(insert_stmt, data)
    db.commit()
    message = "File saved successfully"
    db.close()
    return render_template('result.html', message=message)


if __name__ == '__main__':

    app.run(host='*****', port=port)