from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import smtplib
from email.message import EmailMessage
import mysql.connector
import datetime
from typing import Dict, Optional
import threading
import subprocess

app = FastAPI()
app.add_middleware( #so physical phone can commnicate with fastapi server
    CORSMiddleware,
    allow_origins=[""],
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)
#------------------------------------------------
#REACT NATIVE ENDPOINTS
#EMAIL TO BE USED TO SEND TO USERS
def send_otp(to_email, otp):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    from_mail = 'bigbackclock100@gmail.com'
    server.login(from_mail, 'jmfk xtia prma zdpn')
    msg = EmailMessage()
    msg['Subject'] = 'OTP'
    msg['From'] = from_mail
    msg['To'] = to_email
    msg.set_content(otp)
    server.send_message(msg)
user= {}
'''def db_connection():
    return mysql.connector.connect(
        user='root',
        password='Nahida77@',
        host='localhost',
        database='nutri_genie',
    )'''
def db_connection():
    return mysql.connector.connect(
        host= 'sql12.freesqldatabase.com',
        user= 'sql12735691',
        password= 'Eg6N9EdTWb',
        database= 'sql12735691'
    )
def delete_user():
    cnx = db_connection()
    cursor = cnx.cursor()
    user_id=3
    query = "DELETE FROM nutri_genie.django_app_user WHERE userId = %s"
    #query = "DELETE FROM nutri_genie.django_app_weightprogress WHERE user_id = %s"
    #query = "DELETE FROM nutri_genie.django_app_allergy WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    #if cursor.rowcount == 0:
        #raise HTTPException(status_code=404, detail="User not found")
    #query = "ALTER TABLE nutri_genie.django_app_user AUTO_INCREMENT = 1"
    #query = "ALTER TABLE nutri_genie.django_app_weightprogress AUTO_INCREMENT = 1"
    #query = "ALTER TABLE nutri_genie.django_app_allergy AUTO_INCREMENT = 1"
    #cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()


#SIGNUP
class SignupData(BaseModel):
    username: str
    email: str
    password: str
@app.post("/signup/")
async def signup(signup_data: SignupData):
    otp=""
    for i in range(4):
        otp+=str(random.randint(0,9))
    send_otp(signup_data.email, otp)
    user["username"] = {signup_data.username}
    user["email"]={signup_data.email}
    user["password"]={signup_data.password}
    #print("Received signup data:", signup_data) 
    return {"message": "Signing up", "user": signup_data, "otp": otp}
'''@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}'''

#FIRSTINFO
class FirstinfoData(BaseModel):
    age: int
    weight: float
    height: float
    allergies: list[str]
    gender: str = None
    bmi: float = None
@app.post("/firstinfos/")
async def firstinfo(firstinfo_data: FirstinfoData):
    bmi = round(firstinfo_data.weight / ((firstinfo_data.height / 100) ** 2), 2)
    firstinfo_data.bmi = bmi
    user.update({"age": firstinfo_data.age, "gender": firstinfo_data.gender,"weight":firstinfo_data.weight,"height":firstinfo_data.height,"bmi":bmi, "allergies": firstinfo_data.allergies})
    print('DICTIONARY', user)
    #print("Received first info data:", firstinfo_data, "bmi:", firstinfo_data.bmi) 
    #return {"message": "User created successfully", "user": firstinfo_data}
    return {"message": "First info: ", "BMI": firstinfo_data.bmi}
#BMI
@app.get("/getbmi/")
async def getbmi():
    bmiData = user['bmi']
    return {"message": "BMI calculated", "BMI": bmiData}
#HEALTHGOAL
class HealthGoal(BaseModel):
    healthgoal: str
@app.post("/healthgoal/")
async def healthgoal(healthgoal_data: HealthGoal):
    user.update({"health_goal": healthgoal_data.healthgoal})
    #connect to MySQL database
    '''cnx = mysql.connector.connect(
        user='root',
        password='Nahida77@',
        host='localhost',
        database='nutri_genie',
    )'''
    db_connection()
    cnx = db_connection()
    cursor = cnx.cursor()
    #insert data into MySQL database
    query = ("INSERT INTO user (email, username, password, height, bmi, health_goal, age, gender) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)")
    email="".join(user["email"]) #convert tuple to string since set is not json serializable
    username="".join(user["username"])
    password="".join(user["password"])
    height = float(user["height"])
    bmi = float(user["bmi"])
    health_goal = "".join(user["health_goal"])
    age = int(user["age"])
    gender = "".join(user["gender"])
    data = (email, username, password, height, bmi, health_goal, age, gender)
    cursor.execute(query, data)
    '''query = "DELETE FROM nutri_genie.django_app_user WHERE userId = %s"
    user_id=1
    cursor.execute(query, (user_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    query = "ALTER TABLE nutri_genie.django_app_user AUTO_INCREMENT = 1"
    cursor.execute(query)'''
    #get the last inserted user_id
    user_id = cursor.lastrowid
    #adding weight
    query = ("INSERT INTO weightprogress (weight_progress, date, user_id) VALUES (%s, %s, %s)")
    weight_progress = float(user["weight"])
    date = datetime.date.today()
    data = (weight_progress, date, user_id)
    cursor.execute(query, data)
    #adding allergies
    allergies = user["allergies"]
    if allergies:
        for allergy in allergies:
            query = ("INSERT INTO allergy (allergy_name, user_id) VALUES (%s, %s)")
            data = (allergy, user_id)
            cursor.execute(query, data)
    cnx.commit()
    cursor.close()
    cnx.close()
    #print('DICTIONARY', user)
    return {"message": "Heath Goal: ", "healthgoal": healthgoal_data.healthgoal}


#SIGNING UP(COMPARE EMAIL)
class CompareEmail(BaseModel):
    email: str
@app.post("/compareemail/")
async def compareemail(compareemail_data: CompareEmail,):
    cnx = cnx = db_connection()
    cursor = cnx.cursor()
    query = ("SELECT * FROM user WHERE email = %s")
    cursor.execute(query, (compareemail_data.email,))
    if cursor.fetchone():
        otp = ""
        for i in range(4):
            otp += str(random.randint(0, 9))
        send_otp(compareemail_data.email, otp)
        return {"error": "Email already in use", "otp": otp}
    else:
        return {"message": "Email is available"}
    

#CHANGE PASSWORD
class Password(BaseModel):
    password: str
    email: str
@app.post("/getemail/")
async def getemail(password_data: Password):
    cnx = cnx = db_connection()
    cursor = cnx.cursor()
    query = ("SELECT * FROM user WHERE email = %s")
    cursor.execute(query, (password_data.email,))
    if cursor.fetchone():
        otp = ""
        for i in range(4):
            otp += str(random.randint(0, 9))
        send_otp(password_data.email, otp)
        print(password_data.email,"   password:  " ,password_data.password)
        return {"message": "OTP is sent to your email", "otp": otp, "password_data": {"email": password_data.email, "password": password_data.password}}
    else:
        return {"error": "User is not available"}
@app.post("/changepassword/")
async def changepassword(password_data: Password):
    cnx = cnx = db_connection()
    cursor = cnx.cursor()
    query = ("UPDATE user SET password = %s WHERE email = %s")
    cursor.execute(query, (password_data.password, password_data.email))
    cnx.commit()
    return {"message": "Password updated successfully"}


#LOGIN
class LoginData(BaseModel):
    email: str
    password: str
@app.post("/login/")
async def login(login_data: LoginData):
    '''delete_user()
    return {"message": "Login successfully"}
    '''
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("SELECT * FROM user WHERE email = %s")
    cursor.execute(query, (login_data.email,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="It doesn't have an account")
        #return {"Account": "It doesn't have an account"}
    else:
        query = ("SELECT password FROM user WHERE email = %s")
        cursor.execute(query, (login_data.email,))
        stored_password = cursor.fetchone()[0]
        if stored_password != login_data.password:
            raise HTTPException(status_code=401, detail="Password is incorrect")
            #return {"Password": "Password is incorrect"}
        else:
            user_data = {
                "email": user[1],  # assuming email is the second column
                "userId": user[0],  # assuming userId is the first column
            } 
            return {"message": "Login successfully", "userData": user_data} #'''
        
#GET USERID
class userData(BaseModel):
    email: str
@app.post("/getuserid/")
async def getuserid(email_data: userData):
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("SELECT userId FROM user WHERE email = %s")
    cursor.execute(query, (email_data.email,))
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        print(user_id)
        return {"userId": user_id}
    else:
        return {"error": "User not found"}


#GET DB DATA
class UserData(BaseModel):
    user_id: int
@app.post("/user_data/")
async def get_user_data(user_data: UserData):
    cnx = db_connection()
    cursor = cnx.cursor()
    # retrieve the user data from django_app_user table
    query = ("SELECT username, height, bmi, health_goal, age, gender FROM user WHERE userId = %s")
    cursor.execute(query, (user_data.user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    user_info = {
        "username": user_row[0],
        "height": user_row[1],
        "bmi": user_row[2],
        "health_goal": user_row[3],
        "age": user_row[4],
        "gender": user_row[5],
    }
    # retrieve the latest weight data from django_app_weightprogress table
    #query = ("SELECT weight_progress, weightId, date FROM django_app_weightprogress WHERE user_id = %s ORDER BY date DESC LIMIT 1")
    query = ("SELECT weight_progress, weightId, date FROM weightprogress WHERE user_id = %s ORDER BY date DESC, weightId DESC LIMIT 1")
    cursor.execute(query, (user_data.user_id,))
    weight_row = cursor.fetchone()
    if weight_row:
        weight_data = {
            "weight": weight_row[0],
            "weightId": weight_row[1],
            "date": weight_row[2]
        }
    else:
        weight_data = None
    # retrieve the allergy data from django_app_allergy table
    query = ("SELECT allergy_name, allergyId FROM allergy WHERE user_id = %s")
    cursor.execute(query, (user_data.user_id,))
    allergy_rows = cursor.fetchall()
    allergy_data = [{"allergy_name": row[0], "allergyId": row[1]} for row in allergy_rows]
    # cursor.close()
    # cnx.close()

    print(weight_data)
    return {"user_info": user_info, "weight_data": weight_data, "allergy_data": allergy_data}

#EDIT DB
class EditData(BaseModel):
    user_id: int
    age: int
    gender: str
    height: float
    bmi: float
    healthgoal: str
    allergy_id: Dict[str, Optional[int]] = {}
    weight_id: int
    weight: int
@app.post("/edit_data/")
async def create_user_data(edit_data: EditData):
    print(edit_data)
    cnx = db_connection()
    cursor = cnx.cursor()
    #user data
    query = ("UPDATE user SET height = %s, bmi = %s, health_goal = %s, age = %s, gender = %s WHERE userId = %s")
    cursor.execute(query, (edit_data.height, edit_data.bmi, edit_data.healthgoal, edit_data.age, edit_data.gender, edit_data.user_id))
    #weight progress
    query = ("UPDATE weightprogress SET weight_progress = %s WHERE weightId = %s")
    cursor.execute(query, (edit_data.weight, edit_data.weight_id))
    #allergies
    for allergy_name, allergy_id in edit_data.allergy_id.items():
        if allergy_id is None:
            #new allergy
            query = ("INSERT INTO allergy (allergy_name, user_id) VALUES (%s, %s)")
            cursor.execute(query, (allergy_name, edit_data.user_id))
        else:
            #udate existing allergy
            query = ("UPDATE allergy SET allergy_name = %s WHERE allergyId = %s")
            cursor.execute(query, (allergy_name, allergy_id))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "edit data received successfully"}
class RefreshBMI(BaseModel):
    user_id: int
    bmi: float
@app.post("/refresh_bmi/")
async def refresh_user_bmi(bmi: RefreshBMI):
    print(bmi)
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("UPDATE user SET bmi = %s WHERE userId = %s")
    cursor.execute(query, (bmi.bmi, bmi.user_id))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "update bmi received successfully"}

#DELETE ALLERGY
class DeleteAllergyData(BaseModel):
    allergyId: int
@app.post("/delete_allergy/")
async def delete_allergy(allergy_data: DeleteAllergyData):
    allergy_id = allergy_data.allergyId
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("DELETE FROM allergy WHERE allergyId = %s")
    cursor.execute(query, (allergy_id,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "allergy deleted successfully"}

#HOMEPAGE
#GET ALL WEIGHT
class WeightRequest(BaseModel):
    user_id: int
@app.post("/weights/") #accepts json body
def get_weights(request: WeightRequest):
    connection = db_connection()
    cursor = connection.cursor()
    query = "SELECT weightId, date, weight_progress FROM weightprogress WHERE user_id = %s"
    cursor.execute(query, (request.user_id,))
    weights = cursor.fetchall()
    result = {}
    for weight in weights:
        result[weight[0]] = {"date": weight[1], "weight": weight[2]}
        #print(result)
    return result
'''@app.get("/weights/{user_id}") #accepts path params
def get_weights(user_id: int):
    connection = db_connection()
    cursor = connection.cursor()
    query = "SELECT weightId, date, weight_progress FROM weights WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    weights = cursor.fetchall()
    result = {}
    for weight in weights:
        result[weight[0]] = {"date": weight[1], "weight": weight[2]}
    print(result)
    return result
#REACT to send user_id as a path param
useEffect(() => {
  fetch(`http://192.168.x.x:8000/weights/${userId}`, {
    method: 'GET',
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
}, [userId]);'''
class WeightData(BaseModel):
    weight: float
    date: str
    user_id: int
@app.post("/add_weight/")
async def add_weight(data: WeightData):
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("INSERT INTO weightprogress (weight_progress, date, user_id) VALUES (%s, %s, %s)")
    cursor.execute(query, (data.weight, data.date, data.user_id))
    print(data.weight, data.date, data.user_id)
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Weight data added successfully"}
#delete weight
class DeleteWeightData(BaseModel):
    weightId: int
@app.post("/delete_weight/")
async def delete_weight(data: DeleteWeightData):
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("DELETE FROM weightprogress WHERE weightId = %s")
    cursor.execute(query, (data.weightId,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Weight data deleted successfully"}
class UpdateWeightData(BaseModel):
    weightId: int
    weight: float
@app.post("/update_weight/")
async def update_weight(data: UpdateWeightData):
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("UPDATE weightprogress SET weight_progress = %s WHERE weightId = %s")
    cursor.execute(query, (data.weight, data.weightId))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Weight data updated successfully"}
class DeleteWeightData(BaseModel):
    userId: int
@app.post("/check_delete/")
async def check_delete(data: DeleteWeightData):
    cnx = db_connection()
    cursor = cnx.cursor()
    query = ("SELECT COUNT(*) FROM weightprogress WHERE user_id = %(user_id)s")
    cursor.execute(query, {"user_id": data.userId})
    num_entries = cursor.fetchone()[0]
    if num_entries <= 1:
        return {"message": "Cannot delete all weight data"}
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Weight data deleted successfully"}
#COMPARE BMI

#DIET GENERATOR SCREEN
user_id_cache = 0
def run_script():
    subprocess.Popen(["python", "test_model.py"])
class UserIdRequest(BaseModel):
    userId: int
@app.post("/user/")
async def read_user_id(request: UserIdRequest):
    global user_id_cache
    user_id_cache = request.userId
    response = {"received_user_id_api": request.userId}
    threading.Thread(target=run_script).start()
    return response
@app.get("/get-user-id")
async def get_user_id():
    global user_id_cache
    #return {"userId": user_id_cache}
    cnx = db_connection()
    cursor = cnx.cursor()
    # Get user info from nutri_genie.django_app_user
    query = "SELECT height, age, gender, health_goal FROM user WHERE userId = %s"
    cursor.execute(query, (user_id_cache,))
    user_info = cursor.fetchone()
    # Get latest weight progress from nutri_genie.django_app_weightprogress
    query = "SELECT weight_progress FROM weightprogress WHERE user_id = %s ORDER BY date DESC, user_id DESC LIMIT 1"
    cursor.execute(query, (user_id_cache,))
    latest_weight_progress = cursor.fetchone()
    # Get list of allergy names from nutri_genie.django_app_allergy
    query = "SELECT allergy_name FROM allergy WHERE user_id = %s"
    cursor.execute(query, (user_id_cache,))
    allergy_rows = cursor.fetchall()
    allergy_names = [row[0] for row in allergy_rows]
    # Return the data
    return {
        "user_info": {
            "height": user_info[0],
            "age": user_info[1],
            "gender": user_info[2],
            "health_goal": user_info[3]
        },
        "latest_weight_progress": latest_weight_progress[0] if latest_weight_progress else None,
        "allergy_names": allergy_names
    }
