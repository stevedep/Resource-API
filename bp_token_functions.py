import json
import time

def fn_GetMinutesLeft(strava_tokens, username):
    # calculate the number of days left for each user
    from datetime import datetime        
    at = strava_tokens[username]['expires_at']
    # now to epoc time
    now = datetime.now().timestamp()
    # calculate the number of minutes left
    minutes_left = (at - now) / 60
    return minutes_left