'''
@author Dillon Carns
@version 08/30/2018
'''
import socket
import cv2
import pickle
import json
from time import sleep


HOST = ''
PORT = 0

def createDataSet(clientSocket, fullName, course, cam):
    '''
    Will tell server that new user is being added
    :param clientSocket: maintains socket at current ip
    '''
    clientSocket.send(("create"+fullName+'#'+course).encode())
    sampleNum = 0
    while True:
        sampleNum += 1
        ret, img = cam.read()
        # img is in color, but need grayscale image to function
        #send grayscale frame to server for face extraction
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dataToSend = pickle.dumps(gray)
        try:
            clientSocket.send(str(len(dataToSend)).encode())
            sleep(0.1)
            clientSocket.send(dataToSend)
        except Exception as e:
            continue

        if sampleNum > 20:
            break
    try: #try to see if client is in system
        response = clientSocket.recv(1024).decode()
    except Exception as e:
        return False
    if response[:3] == "YES":
        return True
    else:
        return False


def signInUser(clientSocket, firstname, lastname, course):
    '''
    responsible for signing in user
    :param clientSocket: socket to send data on
    :param firstname: firstname of user from ui
    :param lastname: last name of user from ui
    :param course: course of user from ui
    '''
    user_info = 'signin' + str(firstname) + ' ' + str(lastname) + ' ' + str(course)
    clientSocket.send(user_info)


def RecognizeClient(clientSocket, cam):
    '''
    Responsible for taking a picture, sending to server for recognition
    and attendance to then be recorded
    :param clientSocket: maintains socket connection at current ip
    :return:
    '''
    clientSocket.send("recognize".encode())
    # Need video capture object
    try:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        return False
    data_string = pickle.dumps(gray)
    #print(len(data_string))
    clientSocket.send(data_string)
    try: #try to see if client is in system
        response = clientSocket.recv(1024).decode()
    except Exception as e:
        response = 'NO'
    if response[:3] == "YES":
        return response[3:]
    else:
        return False



def initialize():

    try:
        with open('client_config.json') as f:
            client_conf = json.load(f)
    except Exception as msg:
        return None
    HOST = client_conf["HOST"]
    PORT = int(client_conf["PORT"])

    try:
        clientSocket = socket.socket()
        clientSocket.connect((HOST, PORT))
    except Exception as msg:
        return None

    return clientSocket

