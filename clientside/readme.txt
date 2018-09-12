This is the client side of the facial recognition attendance application.
The purpose is to be able to communicate with the server specified in the 
client_config.json file.
The server will either sign a user in, or sign a user out like a normal attendance.
However, a user has the option to create a recognition dataset and then can click recognize,
which will then tell the server to capture 20 images of the user and train with an LBPH 
algorithm provided by opencv contribs to identify user in the future and sign them in.
Then a user can use the recognize feature to auto fill user information so a user may 
sign in or out easier in the future.

This is a networked application in the hopes that multiple computers could potentially 
connect and use simultaneously. 

The main method is found in in ClientInterface.py
