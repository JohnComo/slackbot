import slack 
import os 
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import string 
from datetime import datetime, timedelta

env_path = Path('.') / '.env'
load_dotenv(dotenv_path = env_path)

app = Flask(__name__)

# Holds events 
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token = os.environ['SLACKBOT_TOKEN'])

BOT_ID = client.api_call("auth.test")['user_id']

# resets when the server is shut down 
message_counts = {}
welcome_messages = {}

BAD_WORDS = ['bad', 'cheating', 'tester bad word']

SCHEDULED_MESSAGES = [ 
    {'text': 'First scheduled message', 'post_at': (datetime.now() + timedelta(seconds=40)).timestamp() , 'channel': 'C021BS5PMDW'},
    {'text': 'Second scheduled message', 'post_at': (datetime.now() + timedelta(seconds=60)).timestamp() , 'channel': 'C021BS5PMDW'}
]

class WelcomeMessage: 
    START_TEXT = { 
        'type':'section', 
        'text': { 
            'type':'mrkdwn', 
            'text': ( 
                'Welcome to this awesome channel! \n\n'
                '*Get started by completing the tasks!*'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(self, channel, user): 
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False

    def get_message(self): 
        return {
            'ts': self.timestamp, 
            'channel':self.channel, 
            'username': 'Welcome Robot', 
            'icon_emoji': self.icon_emoji, 
            'blocks': [
                self.START_TEXT, 
                self.DIVIDER, 
                self._get_reaction_task()
            ]
        }

    def _get_reaction_task(self): 
        checkmark = ':white_check_mark:'
        if not self.completed: 
            checkmark = ':white_large_square:'

        text = f'{checkmark} *React to this message!*'

        return {'type': 'section', 'text':{'type': 'mrkdwn', 'text':text}}


def send_welcome_message(channel, user):
    if channel not in welcome_messages: 
        welcome_messages[channel] = {}

    if user in welcome_messages[channel]: 
        return 

    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    welcome_messages[channel][user] = welcome

def schedule_messages(messages): 
    ids = []
    for msg in messages: 
        response = client.chat_scheduleMessage(channel = msg['channel'], text = msg['text'], post_at = msg['post_at']).data
    id_ = response.get('scheduled_message_id')
    ids.append(id_)

    return ids

def delete_scheduled_message(ids, channel): 
    for _id in ids: 
        client.chat_deleteScheduledMessage(channel = channel, scheduled_message_id = _id)

def handle_bad_words(message): 
    msg = message.lower()
    msg = msg.translate(str.maketrans('', '', string.punctuation)) 

    return any(word in msg for word in BAD_WORDS)  


@slack_event_adapter.on('message')
def message(payload): 
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    # makes sure bot isnt answering itself 
    if user_id != None and BOT_ID != user_id: 
        if user_id in message_counts: 
            message_counts[user_id] += 1
        else: 
            message_counts[user_id] = 1

        if text.lower() == 'start':
            send_welcome_message(f'@{user_id}', user_id)
        elif handle_bad_words(text):
            ts = event.get('ts') 
            client.chat_postMessage(channel=channel_id, thread_ts = ts, text = 'THAT IS A BAD WORD' )

        #client.chat_postMessage(channel = channel_id, text = text)

@slack_event_adapter.on('reaction_added')
def reaction(payload): 
    event = payload.get('event', {})
    channel_id = event.get('item',{}).get('channel')
    user_id = event.get('user')

    if f'@{user_id}' not in welcome_messages: 
        return 

    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']



# Endpoint to hold slash command 
# Default is only GET 
@app.route('/message-count', methods = ['POST'])
def message_count():
    data = request.form 
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get(user_id, 0)
    client.chat_postMessage(channel = channel_id, text = 'Messages {0}'.format(message_count))
    return Response(), 200

if __name__ == "__main__": 
    ids = schedule_messages(SCHEDULED_MESSAGES)
    #delete_scheduled_message(ids, 'C021BS5PMDW')
    app.run(debug = True, port = 4000)
