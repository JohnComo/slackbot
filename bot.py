from flask import Flask 
import slackclient # allows us to send messages and do things on our behalf
import slackeventsapi # allows us to get events from our slack and use them

app = Flask(__name__)

@app.route('/')
def hello_world(): 
    return('Hello World')

if __name__ == '__main__': 
    app.run(host = '0.0.0.0', port = 8080); 