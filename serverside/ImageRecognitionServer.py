'''
@author Dillon Carns
@version 08/30/2018
'''
import socket
import threading
import sys
import os
import cv2
import numpy as np
import datetime
import pickle
import gspread
import json
from PIL import Image
from cv2 import face
from DatabaseHandler import *
from oauth2client.service_account import ServiceAccountCredentials


"""
Server code
listens for client to say that its either going to create a new data
or needs to recognize (facial recognition) a user and update data accordingly
"""

class Counter:
    usersToSignOut = None
    numActiveUsers = 0
    def __init__(self):
        self.numActiveUsers = 0
        self.usersToSignOut = np.zeros(100, object)

def initialize(host, port):
    '''
    Initializes server socket
    :param host: ip address (string), ex 192.168.4.4
    :param port: port of host (string), ex 9432
    :return: serverSocket, the socket made from host and port
    '''
    serverSocket = socket.socket()
    serverSocket.bind((host, port))
    return serverSocket

def initiateUser(name, clientSocket, server_conf, spread_sheet):
    '''
    Attempt to see if user means to create account or sign in
    :param name: name of method for thread
    :param clientSocket: socket of client connecting to server
    '''

    count = Counter()
    #see if user requested to create dataset or be recognized for sign in
    while clientSocket:
        try:
            userResponse = str(clientSocket.recv(128).decode())
        except Exception as e:
            continue
        #print(userResponse)
        if userResponse[:6] == 'create':
            createUserDataSet(userResponse[6:], clientSocket, server_conf)
        elif userResponse[:6] == 'signin':
            signUserInorOut(userResponse[6:], server_conf, clientSocket, count)
        elif userResponse == 'recognize':
            recognizeUser(clientSocket, server_conf)
        elif userResponse == 'sysend':
            signAllOut(spread_sheet, count)
            break
    try:
        addr = clientSocket
        clientSocket.shutdown(1)
        clientSocket.close()
        print('Client Socket successfully closed from -> ' + str(addr))
    except Exception as e:
        print('Client Socket forcibly closed.')
        return

def signUserInorOut(user_data, server_conf, clientSocket, count):
    '''
    Signs in user after client has filled out data
    :param user_data: user data from client
    :param server_conf: server config file
    '''
    user_name, course = user_data.split('#')
    db_name = server_conf["database_name"]
    profile = getProfileWithName(user_name, db_name)
    if profile != None:
        if profile[8] == 0:
            clientSocket.send('SIN'.encode())
            signUserIn(profile[0], course, profile[3], db_name)
        elif profile[8] == 1:
            clientSocket.send('SNO'.encode())
            signOutUser(profile, db_name, count)
    else:
        clientSocket.send('SIN'.encode())
        id = generateID(db_name) #must be new user so make a new id and add them to database (signed in)
        insertOrUpdate(id, user_name, db_name)
        signUserIn(id, course, user_name, db_name)
    return

def createUserDataSet(clientData, clientSocket, server_conf):
    '''
    Creates a new dataset for user
    :param clientName: string containing full name of user to input
    :param clientSocket: socket from client machine
    '''

    data_path = server_conf["data_path"]
    training_path = server_conf["training_path"]
    training_filename = server_conf["training_data"]
    db_name = server_conf["database_name"]

    id = generateID(db_name)
    clientName, course = clientData.split('#')
    insertOrUpdate(id, clientName, db_name)
    #receive new images for training - 20 every user
    sampleNum = 0
    temp = None
    yes = True
    while True:

        sampleNum += 1
        try :
            x = clientSocket.recv(307362)
            while len(x) < 307362:
                x += clientSocket.recv(64)
            gray = pickle.loads(x)
            temp = gray
        except Exception as e:
            print("Lost connection with user, attempting to use last found image..")
            if temp is not None:
                gray = temp
            else:
                print('Could not find image')
                if sampleNum < 21:
                    continue
                else:
                    break

        # detects all faces in current frame
        faceDetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        faces = faceDetect.detectMultiScale(gray, 1.3, 5)
        imageName = data_path+"User." + str(id) + "." + str(sampleNum) + ".jpg"
        print('creating image: ' + str(sampleNum) + 'for user id: ' + str(id))
        for (x, y, w, h) in faces:
            cv2.imwrite(imageName, gray[y:y + h, x:x + w]) #write image to server directory dataset

        if sampleNum > 20:
            yes = True
            clientSocket.send('YES'.encode())
            break

    if yes:
        train(data_path, training_path, training_filename)
        profile = getProfile(id, db_name)
        signUserIn(id, course, profile[3], db_name)
    else:
        return


def recognizeUser(clientSocket, server_conf):
    '''
    Recognizes user and returns id for database update
    :param clientSocket:
    :return: id, int
    '''
    rec = cv2.face.LBPHFaceRecognizer_create()
    rec.read("recognizer/trainingdata.yml")
    #compare against image captured from user
    db_name = server_conf["database_name"]
    #acquire image from client's webcam
    data_arr = clientSocket.recv(307362)
    while len(data_arr) < 307362:
        data_arr += clientSocket.recv(64)
    gray = pickle.loads(data_arr)

    faceDetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    faces = faceDetect.detectMultiScale(gray, 1.3, 5)
    profile = None
    for (x, y, w, h) in faces:
        id, conf = rec.predict(gray[y:y + h, x:x + w])
        profile = getProfile(id, db_name)
        course = ''
        if (profile[6] == '' or profile[6] == None):
            course = ''
        else:
            course = ' ' + str(profile[6])

    if profile != None:
        clientSocket.send(("YES"+str(profile[3]+course)).encode())
    else:
        clientSocket.send("NO".encode())



def signUserIn(id, course, name, db_name):
    '''
    Utilize user id to sign in, once confirmed
    :param id: the id # of user derived from database (array)
    :param course: the course number that the user would like to sign-in for
    '''
    print('signing in ' + str(name))
    conn = sqlite3.connect(db_name)
    now = datetime.datetime.now()
    day = now.isoweekday()
    if day == 1:
        day = "Monday"
    elif day == 2:
        day = "Tuesday"
    elif day == 3:
        day = "Wednesday"
    elif day == 4:
        day = "Thursday"
    elif day == 5:
        day = "Friday"
    elif day == 6:
        day = "Saturday"
    elif day == 7:
        day = "Sunday"
    date = now.strftime("%m/%d/%Y")
    if now.hour > 11:
        time = now.strftime("%I:%M") + " PM"
    else:
        time = now.strftime("%I:%M") + " AM"
    cmd = "UPDATE Students SET Date=\"" + str(date) + "\", " \
            + "Weekday =\"" + str(day) + "\", " \
            + "Time_In =\"" + str(time) + "\", " \
            + "Subject =\"" + str(course) + "\", " \
            + "SignedIn =\"" + str(1) + "\" " \
            + "WHERE ID =\"" + str(id) + "\";"
    conn.execute(cmd)
    conn.commit()
    conn.close()
    return

def signOutUser(profile, db_name, count):
    '''
    Methods to sign a specific user out
    :param profile: profile of user fetched from database in earlier method
    '''
    print('signing out user: ' + profile[3])
    now = datetime.datetime.now()
    if now.hour > 11:
        time = now.strftime("%I:%M") + " PM"
    else:
        time = now.strftime("%I:%M") + " AM"
    conn = sqlite3.connect(db_name)
    cmd = "UPDATE Students SET Time_Out=\"" + str(time) + "\", " \
          + "SignedIn =\"" + str(0) + "\" " \
          + "WHERE ID =\"" + str(profile[0]) + "\";"
    conn.execute(cmd)
    conn.commit()
    conn.close()
    print()
    count.usersToSignOut[count.numActiveUsers] = getProfile(int(profile[0]), db_name)
    count.numActiveUsers += 1



def getImagesWithID(path):
    '''
    Methods to return all images within a directory
    :param path: path to directory of images - configured in json file
    '''
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    IDs = []
    for imagePath in imagePaths:
        # opencv only works with numpy array
        # this converts image from path to python image type(PIL)
        faceImg = Image.open(imagePath).convert('L')
        faceNp = np.array(faceImg, 'uint8')
        # need to split the path to get user id and convert to int
        ID = int(os.path.split(imagePath)[-1].split('.')[1])
        faces.append(faceNp)
        IDs.append(ID)

    return np.array(IDs), faces

def train(path, training_path, training_filename):
    '''
    This trains the dataset whenever a new user is added
    :param path: this is the path to dataset data (images directory) - configured in json file
    '''
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    IDs, faces = getImagesWithID(path)
    recognizer.train(faces, IDs)
    recognizer.write(training_path + training_filename)
    cv2.destroyAllWindows()


def signAllOut(spread_sheet, count):
    '''
    Responsible for signing all users out at once.
    Useful when a session ends and users forget or remain.
    '''
    for i in range(0, count.numActiveUsers):
        profile = count.usersToSignOut[i]
        weekday = str(profile[2])
        date = str(profile[1])
        name = str(profile[3])
        time_in = str(profile[4])
        time_out = str(profile[5])
        course = str(profile[6])
        updateSpreadSheet(weekday, date, name, time_in, time_out, course, spread_sheet)

    print('All user data (if any for session) finished updating in spread sheet.')



def updateSpreadSheet(weekday, date, name, time_in, time_out, course, spread_sheet):
    '''
    Simply appends required data to spread sheet upon sign out
    :param profile:  derived from database, to update sheet cell data
    '''

    rowNum = 1
    while(spread_sheet.cell(int(rowNum), 1).value not in ['None', None, '']):
        rowNum += 1
    spread_sheet.update_cell(rowNum, 1, weekday)
    spread_sheet.update_cell(rowNum, 2, date)
    spread_sheet.update_cell(rowNum, 3, name)
    spread_sheet.update_cell(rowNum, 4, time_in)
    spread_sheet.update_cell(rowNum, 5, time_out)
    spread_sheet.update_cell(rowNum, 6, course)



def main():
    '''
    main method to run server - please ensure json file is configured before use
    '''

    try:
        with open('server_config.json') as f:
            server_conf = json.load(f)
        HOST = str(server_conf["HOST"])#sys.argv[1] - configured in json
        PORT = int(server_conf["PORT"])  #sys.argv[2] - configured in json
    except Exception as msg:
        print(msg)
        sys.exit(0)
    #initialize serversocket
    try:
        serverSocket = initialize(HOST, PORT)
        serverSocket.listen(8)
    except Exception as msg:
        print(msg)
        sys.exit(0)
    ON_OFF = True

    try:
        scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

        g_key_filename = str(server_conf["google_api_credentials"])
        g_sheet_name = str(server_conf["google_sheet_name"])

        credentials = ServiceAccountCredentials.from_json_keyfile_name(g_key_filename, scope)
        gc = gspread.authorize(credentials)
        spread_sheet = gc.open(g_sheet_name).sheet1
    except Exception as e:
        print(e)
        print('Failed to connect to spread sheet. Now exiting.')
        sys.exit(2)
    print("Server Session Initialized Successfully")
    while True:
        #handle each client machine on different threads
        try:
            clientSocket, clientAddr = serverSocket.accept()
            print("Client connected from: <" + str(clientAddr) + ">")
            clientThread = threading.Thread(target=initiateUser, args=("initiateUser", clientSocket, server_conf, spread_sheet))
            clientThread.start()
        except socket.error as msg:
            print(msg)

    try:
        serverSocket.shutdown(1)
        serverSocket.close()
    except Exception as msg:
        sys.exit(2)
        print('Forcibly Shutdown.')
    print('Successfully shutdown.')
    sys.exit(1)


if __name__ == '__main__':
    main()






