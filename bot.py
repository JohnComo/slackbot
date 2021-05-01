from flask import Flask 
from slack import WebClient # allows us to send messages and do things on our behalf
import slackeventsapi # allows us to get events from our slack and use them
from slackeventsapi import SlackEventAdapter
import random
import os 
import secrets


app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(os.environ.get(secrets.SLACK_EVENTS_TOKEN), "/slack/events", app)

slack_web_client = WebClient(token = os.environ.get(secrets.SLACKBOT_TOKEN))

# Template for how slack sends message
MESSAGE_BLOCK = { 
    "type":"section", 
    "text": { 
        "type":"mrkdwn", 
        "text":""
    }
}

# These are the events handlers made by slack so there is emoji, image, etc 
@slack_events_adapter.on("message")
def message(payload): 
    
    event = payload.get("event",{})

    text = event.get("text")

    if "flip a coin" in text.lower(): 

        channel_id = event.get("channel")

        rand_int = random.rand_int(0,1)

        if (rand_int == 0): 
            result = "Heads"
        else: 
            result = "Tails"
    
        message = f"The result is {result}"

        MESSAGE_BLOCK["text"]["text"] = message
        message_to_send = {"channel": channel_id, 
                     "blocks": {MESSAGE_BLOCK}}

        return slack_web_client.chat_postMessage(**message_to_send)

        

if __name__ == '__main__': 
    app.run(host = '0.0.0.0', port = 8080); 