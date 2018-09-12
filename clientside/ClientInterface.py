'''
@author Dillon Carns
@version 09/11/2018
'''
import sys
import tkinter as tk
from tkinter import font  as tkfont
from PIL import ImageTk, Image
from ImageRecognitionClient import *
from time import sleep

class AttendanceApp(tk.Tk):
    clientSocket = None
    cam = None
    CLASSES = None
    CONNECTED = False
    def __init__(self, *args, **kwargs):
        '''
        Overseeing class, responsible for creating the necessary frames.
        :param args:  args passed to tk init
        :param kwargs:  kwargs passed to tk init
        '''
        tk.Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.dialogue_font = tkfont.Font(family='Times', size=14, weight="bold")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        try:
            self.cam = cv2.VideoCapture(0)
            self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
            self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
            self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        except Exception as e:
            sys.exit(0)
        self.CLASSES = [
            "1100-Discrete Mathematics",
            "1440-Computer Science 1",
            "1445-INTRO TO PROGMG IDS APPLICATIONS",
            "2440-Computer Science 2",
            "2450-Intro to Computer Systems",
            "2490-Intro to Theoretical CS",
            "3100-Junior Seminar",
            "3240-Mobile Programming",
            "3440-Client side Web Programming",
            "3430-Database",
            "3460-Data Structures",
            "3463-Simulation",
            "3481-Computer Systems 1",
            "3482-Computer Systems 2",
            "3490-Programming Languages",
            "3500-Independent Study",
            "3750-Applied Neural Networks",
            "3760-System Admin and Security",
            "3770-Computational Cryptography",
            "3667-Software Engineering",
            "4100-Senior Seminar",
            "4435-Server Side Web Programming",
            "4440-AI",
            "4450-Data Communications and Networking",
            "4465-Computer Graphics",
            "4510-Senior Honors Thesis",
            "4521-Operating Systems",
            "4550-Theoretical Comp Sci",
            "4570-Human Computer Interfaces",
            "4620-Real time Systems",
            "4740-Digital Image Processing",
            "4800-Capstone Project",
        ]

        self.frames = {}
        for F in (StartPage, HomePage, CreateRecognitionPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        windowWidth = self.winfo_reqwidth()
        windowHeight = self.winfo_reqheight()
        positionRight = int(self.winfo_screenwidth() / 2 - windowWidth / 2 - windowWidth)
        positionDown = int(self.winfo_screenheight() / 2 - windowHeight / 2 - windowHeight)
        self.geometry("+{}+{}".format(positionRight, positionDown))
        self.overrideredirect(True)
        self.protocol("WM_DELETE_WINDOW", self.disable_event)
        self.resizable(False,False)
        self.show_frame("StartPage")


    def disable_event(self):
        pass

    def show_frame(self, page_name):
        '''
        Show a frame for the given page name
        :param page_name, the page name is name in string form of wanted frame
        '''
        for frame in self.frames.values():
            frame.grid_remove()
        frame = self.frames[page_name]
        frame.grid()

    def test(self):
        '''
        for testing purposes
        '''
        print('Testing')

    def exit(self):
        '''
        attempts to exit program safely - also signs out all users if a connection was made previously
        '''

        if not self.CONNECTED:
            sys.exit(1)

        try:
            if(self.clientSocket):
                self.clientSocket.send('sysend'.encode())
                frame = self.frames['CreateRecognitionPage']
                frame.cam.release()

                self.clientSocket.shutdown(1)
                self.clientSocke.close()
            else:
                sys.exit(1)
        except Exception as e:
            sys.exit(0)
        sys.exit(1)


class StartPage(tk.Frame):
    '''
    Class is responsible for starting client side
    '''
    controller = None
    info_label = None

    def __init__(self, parent, controller):
        '''
        Constructor for the start page
        Responsible for connecting to server - will not advance until connection established
        :param parent: parent (master) tk unit
        :param controller: controls some over arching methods like switching visible frame and holding client socket
        '''
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.grid()
        self.config(bg='black', width=400, height=400)
        self.winfo_toplevel().title("Help Lab Attendance - Start/Exit Page")

        canvas = tk.Canvas(self, bg='black')
        canvas.grid(row=0, column=0, rowspan=4, columnspan=6, sticky='ew')
        img = tk.PhotoImage("csdept.gif")
        canvas.create_image(0, 0, anchor='nw', image=img)

        canvas2 = tk.Canvas(self, bg='black')
        canvas2.grid(row=4, column=0, rowspan=4, columnspan=6)


        label = tk.Label(self, text="Select Start to Begin Attendance", font=controller.title_font).grid(row=0,column=0, columnspan=6, rowspan=2)

        startButton = tk.Button(self, bg='gold',fg='black', text="Start", font=('times', 16),
                            command=lambda: self.switch_frame()).grid(row=2,column=1, rowspan=1, columnspan = 4, sticky='nsew')
        #change above to self.switchframe
        exitButton = tk.Button(self, bg='gold', fg='black', text="Exit", font=('times', 16),
                            command=lambda: controller.exit()).grid(row=5, column=1, rowspan=1, columnspan=4, sticky='nsew')

        self.info_label = tk.Label(self, text="", font=controller.dialogue_font).grid(row=7,column=0, columnspan=6, rowspan=1)


    def switch_frame(self):
        '''
        inner method to try to switch frame and reset some variables
        does not happen if client socket can not be initialized
        '''
        try:
            self.controller.clientSocket = initialize()
            if self.controller.clientSocket:
                self.controller.show_frame('HomePage')
                self.controller.CONNECTED = True
            else:
                self.info_label = tk.Label(self, text="Failed to connect to host!", font=self.controller.dialogue_font).grid(row=7, column=0,
                                                                                                   columnspan=6,
                                                                                                   rowspan=1)
                self.controller.show_frame('StartPage')
                self.controller.CONNECTED = False
        except Exception as e:
            self.controller.CONNECTED = False
            self.info_label = tk.Label(self, text="Failed to connect to host!", font=self.controller.dialogue_font).grid(row=7,column=0, columnspan=6, rowspan=1)
            self.controller.show_frame('StartPage')


class HomePage(tk.Frame):

    info_label = None
    info_text = ''
    controller = None
    e1 = None
    e2 = None
    e3 = None
    e1Text = None
    e2Text = None
    e3Text = None

    def __init__(self, parent, controller):
        '''
        Constructor for the home page
        Responsible for user interactivity
        :param parent:
        :param controller:
        '''
        tk.Frame.__init__(self, parent)
        self.controller = controller
        background = tk.Canvas(self, bg='black', bd=0, relief='ridge', highlightthickness=0)
        background.grid(row=0, column=0, rowspan=12, columnspan=10, sticky='we')
        msgText = tk.StringVar()
        msgText.set('Please sign in/out or create recognition user')
        label = tk.Label(self, text="Home Page", font=controller.title_font).grid(row=0, column=0, columnspan=10, rowspan=2, sticky='ew')
        msg = tk.Label(self, text=msgText.get(), fg='black', bg='gold', font=('times', 14, 'bold')).grid(row=2,
                                                                                                              column=0,
                                                                                                              columnspan=10,
                                                                                                                rowspan=2,
                                                                                                            sticky='we')

        first_name = tk.Label(self, text="First Name", bg='black', fg='gold', font=('times', 16)).grid(sticky='e',
                                                                                                         row=4,
                                                                                                         column=0)
        last_name = tk.Label(self, text="Last Name", bg='black', fg='gold', font=('times', 16)).grid(sticky='e',
                                                                                                       row=5, column=0)
        course = tk.Label(self, text="Course", bg='black', fg='gold', font=('times', 16)).grid(sticky='e', row=6,
                                                                                                 column=0)
        self.e1Text = tk.StringVar(self)
        self.e2Text = tk.StringVar(self)

        self.e1 = tk.Entry(self, text=self.e1Text)
        self.e1.grid(row=4, column=2, columnspan=8)
        self.e2 = tk.Entry(self, text=self.e2Text)
        self.e2.grid(row=5, column=2, columnspan=8)

        self.e3Text = tk.StringVar(self)
        self.e3Text.set(self.controller.CLASSES[0])
        self.e3 = tk.OptionMenu(self, self.e3Text, *self.controller.CLASSES)
        self.e3['menu'].config(bg='white', fg='black', font=('times', 10))
        self.e3.grid(row=6, column=2, columnspan=8)

        text = 'Please look at camera directly to use recognize.'
        self.info_text = tk.StringVar(self)
        self.info_text.set(text)
        self.info_label = tk.Label(self, text=self.info_text.get(), font=controller.dialogue_font).grid(row=11,
                                                                                                        column=0,
                                                                                                        columnspan=10,
                                                                                                        rowspan=2,
                                                                                                        sticky='ew')

        signInButton = tk.Button(self, text="Sign-in/out", bg='gold', fg='black', font=('times', 10),
                                  command=lambda: self.sign_in_out_client())
        signInButton.grid(row=8, column=0, rowspan=1, columnspan=1, sticky='nsew')

        recognizeButton = tk.Button(self, text="Recognize", bg='gold', fg='black',
                                 command=lambda: self.recognize_user())
        recognizeButton.grid(row=8, column=2, rowspan=1, columnspan=5,sticky='nse')

        createButton = tk.Button(self, text="Create Recognition User", bg='gold', fg='black',
                                 command=lambda: self.switch_frame("CreateRecognitionPage"))
        createButton.grid(row=8, column=9, rowspan=1, columnspan=2,sticky='nsw')

        backButton = tk.Button(self, text="Back", bg='gold', fg='black',
                           command=lambda: controller.show_frame("StartPage"))
        backButton.grid(row=10, column=0, columnspan=1, rowspan=1, sticky='ew')

        for choice in self.controller.CLASSES:
            self.e3['menu'].add_command(label=choice, command=tk._setit(self.e3Text, choice))

    def recognize_user(self):
        '''
        called when user presses recognize, should only be used if user made recognition dataset in the system
        '''
        response = RecognizeClient(self.controller.clientSocket, self.controller.cam)
        if response:
            first_name, last_name, course = response.split(' ')
            self.set_entries(first_name, last_name, course)
            self.set_info_text('Recognized '+first_name+' '+last_name+'.')
        else:
            return

    def sign_in_out_client(self):
        '''
        called when sign/out button is pressed.
        if user is signed out it will sign them in,
        if user is signed in, server should sign them out
        will notify on info bar at bottom of interface
        '''
        first_name = self.e1Text.get()
        last_name = self.e2Text.get()
        course_num, course_name = self.e3Text.get().split('-')
        self.controller.clientSocket.send(str('signin'+first_name + ' ' + last_name + '#' + course_num).encode())
        server_response = self.controller.clientSocket.recv(8).decode()
        if server_response == 'SIN':
            self.set_info_text('Signed in ' + first_name + ' ' + last_name + '.')
        elif server_response == 'SNO':
            self.set_info_text('Signed out ' + first_name + ' ' + last_name + '.')
        while server_response != 'SIN' and server_response != 'SNO':
            print(server_response)
            if server_response == 'SIN':
                self.set_info_text('Signed in ' + first_name + ' ' + last_name + '.')
                break
            elif server_response == 'SNO':
                self.set_info_text('Signed out ' + first_name + ' ' + last_name + '.')
                break
            server_response = self.controller.clientSocket.recv(8).decode()

    def set_entries(self, first_name, last_name, course):
        '''
        Responsible for setting the entries so a user may easily click sign in after recognition
        :param first_name: first name of user found from recognition server
        :param last_name: last name of user found from recognition server
        :param course: last course of user found from recognition server
        :return:
        '''
        self.e1Text = tk.StringVar(self)
        self.e2Text = tk.StringVar(self)
        self.e1Text.set(first_name)
        self.e2Text.set(last_name)
        self.e1 = tk.Entry(self, text=self.e1Text)
        self.e1.grid(row=4, column=2, columnspan=8)
        self.e2 = tk.Entry(self, text=self.e2Text)
        self.e2.grid(row=5, column=2, columnspan=8)
        try:
            menu = self.e3["menu"]
            menu.delete(len(self.controller.CLASSES), "end")
        except Exception as e:
            return
        if course != '' and course != None:
            course_index = 0
            for line in self.controller.CLASSES:
                course_num, course_name = line.split('-')
                if course_num == course:
                    self.e3Text.set(str(self.controller.CLASSES[course_index]))
                    break
                course_index += 1
        else:
            self.e3Text.set(str(self.controller.CLASSES[0]))

    def switch_frame(self, text):
        '''
        inner method to try to switch frame and reset some variables
        does not happen if client socket can not be initialized
        '''
        self.controller.show_frame(text)
        self.set_info_text('Please look at camera directly to use recognize.')


    def set_info_text(self, text):
        '''
        method to set the info bar at bottom of frame
        :param text: text to set info bar text to
        '''
        self.info_text.set(text)
        self.controller.update_idletasks()
        sleep(1)
        self.info_label = self.info_label = tk.Label(self, text=self.info_text.get(), font=self.controller.dialogue_font).grid(row=11,
                                                                                                        column=0,
                                                                                                        columnspan=10,
                                                                                                        rowspan=2,
                                                                                                        sticky='ew')


class CreateRecognitionPage(tk.Frame):

    lmain = None
    text = ''
    info_text = None
    info_label = None
    controller = None
    cam = None
    last_name_field = None
    first_name_field = None
    course_field = None
    last_name_text = None
    first_name_text = None
    course_text = None

    def __init__(self, parent, controller):
        '''
        This is the recognition page which will let some one make a recognition account
        :param parent: tk root - container for the frame stack
        :param controller: controller of container - used to invoke methods
        '''
        tk.Frame.__init__(self, parent)
        self.controller = controller
        background = tk.Canvas(self, bg='black', bd=0, relief='ridge', highlightthickness=0)
        background.grid(row=0, column=0, rowspan=19, columnspan=16, sticky='nswe')
        msgText = tk.StringVar()
        msgText.set('Please look directly at camera, then press GO (this will sign you in after!)')
        label = tk.Label(self, text="Creation of Recognition Dataset", font=controller.title_font).grid(row=0, column=0, columnspan=10,
                                                                                  rowspan=2, sticky='ew')
        msg = tk.Label(self, text=msgText.get(), fg='black', bg='gold', font=('times', 14, 'bold')).grid(row=2,
                                                                                                         column=0,
                                                                                                         columnspan=12,
                                                                                                         rowspan=2,
                                                                                                         sticky='we')
        first_name = tk.Label(self, text="First Name", bg='black', fg='gold', font=('times', 16)).grid(sticky='e',
                                                                                                       row=4,
                                                                                                       column=0)
        last_name = tk.Label(self, text="Last Name", bg='black', fg='gold', font=('times', 16)).grid(sticky='e',
                                                                                                     row=5, column=0)
        course = tk.Label(self, text="Course", bg='black', fg='gold', font=('times', 16)).grid(sticky='e', row=6,
                                                                                               column=0)
        self.first_name_text = tk.StringVar(self)
        self.last_name_text = tk.StringVar(self)

        self.first_name_field = tk.Entry(self, text=self.first_name_text)
        self.first_name_field.grid(row=4, column=2, columnspan=8)
        self.last_name_field = tk.Entry(self, text=self.last_name_text)
        self.last_name_field.grid(row=5, column=2, columnspan=8)
        self.course_text = tk.StringVar(self)
        self.course_text.set(self.controller.CLASSES[0])
        self.course_field = tk.OptionMenu(self, self.course_text, *self.controller.CLASSES)
        self.course_field['menu'].config(bg='white', fg='black', font=('times', 10))
        self.course_field.grid(row=6, column=2, columnspan=8)

        self.cam = self.controller.cam
        self.lmain = tk.Label(self)
        self.lmain.grid(row=7, column=0, rowspan=8, columnspan=10, sticky='nsew')

        backButton = tk.Button(self, text="Back", bg='gold', fg='black',
                               command=lambda: self.switch_frame())
        backButton.grid(row=15, column=0, columnspan=1, rowspan=2, sticky='nsew')

        goButton = tk.Button(self, text="GO", bg='gold', fg='black', command=lambda:self.create_dataset())
        goButton.grid(row=15, column=4, columnspan=1, rowspan=2, sticky='nsew')

        self.info_text = tk.StringVar(self)
        self.text = 'Awaiting User - Look directly at camera before pressing GO.'
        self.info_text.set(self.text)
        self.info_label = tk.Label(self, text=self.info_text.get(), font=controller.dialogue_font).grid(row=17,
                                                                                                        column=0,
                                                                                                        columnspan=10,
                                                                                                        rowspan=2,
                                                                                                        sticky='ew')
    def switch_frame(self):
        '''
        inner method to try to switch frame and reset some variables
        does not happen if client socket can not be initialized
        '''
        self.controller.show_frame('HomePage')
        self.set_info_text('Awaiting user - Look directly at camera before pressing GO.')
    def show_frame(self):
        '''
        responsible for showing webcam in ui
        same cam is used throughout program
        '''
        try:
            ret, img = self.cam.read()
            # img is in color, but need grayscale image to function
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            frame = cv2.flip(gray, 1)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lmain.imgtk = imgtk
            self.lmain.configure(image=imgtk)
            self.lmain.after(10, self.show_frame)
        except Exception as e:
            return

    def create_dataset(self):
        '''
        Notifies server that it will be creating a new user for recognition service.
        This will also sign in that user
        :param name: full name of user to create a data set given user information
        :param course
        '''
        course_num, course = self.course_text.get().split('-')
        name = str(self.first_name_text.get() + ' ' + self.last_name_text.get())
        createDataSet(self.controller.clientSocket, name, course_num, self.controller.cam)
        self.first_name_text.set('')
        self.last_name_text.set('')
        self.course_text.set(str(self.controller.CLASSES[0]))
        self.set_info_text('Created Dataset for: ' + name + ' , Process finished')


    def set_info_text(self, text):
        '''
        method to set the info bar at bottom of frame
        :param text: text to set info bar text to
        '''
        self.info_text.set(text)
        self.controller.update_idletasks()
        sleep(1)
        self.info_label = tk.Label(self, text=self.info_text.get(), font=self.controller.dialogue_font).grid(row=17,
                                                                                                        column=0,
                                                                                                        columnspan=10,
                                                                                                        rowspan=2,
                                                                                                        sticky='ew')

if __name__ == "__main__":
    app = AttendanceApp()
    frame = app.frames['CreateRecognitionPage'].show_frame()
    app.mainloop()
