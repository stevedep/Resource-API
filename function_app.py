import azure.functions as func
import logging
import jwt
import json
import requests
from bp_azure_blob import store_to_container, retreive_from_container
from bp_token_functions import fn_GetMinutesLeft
import datetime
import time
import pandas as pd
from pandas import json_normalize
import json
import csv

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route('User', methods=['GET'])
def get_users(req: func.HttpRequest) -> func.HttpResponse:
    # Handle GET request for /api/users
    token_str = req.headers.get('Authorization')
    if token_str:
        # send token_str to api to get username, performa a get request to api
        url = "http://localhost:7072/api/CheckToken"
        headers = {'Authorization': token_str}
        r = requests.get(url, headers=headers)
        logging.info(r.status_code)
        if r.status_code == 202:
            # get username from responsetext and load into json to then get the userid using that key
            username = json.loads(str(r.text))['userid']
            logging.info(username)
            with open('userid.json') as json_file:
                strava_tokens = json.load(json_file)

            # check if key exists for username
            if username in strava_tokens:
                # add 4 seconds delay
                time.sleep(1)
                return func.HttpResponse("User found", status_code=204)
            else:
                return func.HttpResponse("User not found", status_code=404)
        else:  # checktoken failed
            return func.HttpResponse(
                "No valid authorization header was provided in the request...",
                status_code=r.status_code
            )
    return func.HttpResponse(username)

def create_dataframe(r):
    df = pd.DataFrame(r['distance']['data'])
    df2 = pd.DataFrame(r['time']['data'])
    df3= pd.concat([df, df2], axis=1)
    df_res = pd.concat([df3.shift(1), df3], axis=1)
    df_res.columns = ['dist-1', 'time-1', 'dist', 'time']
    df_res['time_diff'] = df_res['time'] - df_res['time-1']
    df_res['dist_diff'] = df_res['dist'] - df_res['dist-1']
    df_res['speed'] = (df_res['dist_diff'] / df_res['time_diff']) * 3.6
    df_res['sumcumtimediff'] =  df_res.sort_values(by=['speed'], ascending=True)['time_diff'].cumsum()
    df_res['sumcumdistdiff'] =  df_res.sort_values(by=['speed'], ascending=True)['dist_diff'].cumsum()
    time = df_res.loc[df_res['speed'].size-1]['time']
    df_res['percentile'] = (df_res['sumcumtimediff']) / time 
    df_res['percentilerounded'] = round((df_res['percentile'] * 100) , 0) 
    return df_res

def calculate_split(df_res, minutes):
    lst = []
    #minutes = 20
    interval = minutes * 60

    for index, row in df_res.iterrows():    
        if df_res[df_res['time']<=row['time']-interval]['time'].size != 0:
            val = max(df_res[df_res['time']<=row['time']-interval]['time'])
            record = df_res[df_res['time']==val]
            timediff = row['time'] - record['time']
            distdiff = row['dist'] - record['dist']
            speed = (distdiff / timediff) * 3.6
            #print(str(row['time']) + " avg speed " + str(speed.to_string(index=False)))
            lst.append(float(speed.to_string(index=False)))
        else:
            lst.append(0)
    
    
    val = max(lst)
    p = lst.index(val)
    df2 = df_res.filter(items = [p], axis=0)
    
    timeval = max(df_res[df_res['time']<=int(float((df2['time']-(60*minutes)).to_string(index=False)))]['time'])
    kmrecord = df_res[df_res['time']==timeval]
    #print(int(float((df2['time']-(60*minutes)).to_string(index=False))))
    
    
    return [str(round(val,2)), str(int(float(((df2['time']/60)-minutes).to_string(index=False)))),
           str(round(float(((kmrecord['dist']/1000)).to_string(index=False)),2))]


@app.route(route="Get_Activity")
def Get_Activity(req: func.HttpRequest) -> func.HttpResponse:
    token_str = req.headers.get('Authorization')
    activity = req.get_json()
    if token_str:
        # send token_str to api to get username, performa a get request to api
        url = "http://localhost:7072/api/CheckToken"
        headers = {'Authorization': token_str}
        r = requests.get(url, headers=headers)
        logging.info(r.status_code)
        if r.status_code == 202:
            # get username from responsetext and load into json to then get the userid using that key
            username = json.loads(str(r.text))['userid']
            logging.info(username)
            # we will call our function here
            access_token_response = get_access_token(username)
            stcode = access_token_response.status_code
            if stcode == 200:
                access_token = access_token_response.get_body().decode('utf-8')
                logging.info(str(access_token))
                # get activity
                id = activity['activity']['id']
                
                url = "https://www.strava.com/api/v3/activities/" + \
                    str(id) + "/streams/time"
                r = requests.get(url + '?access_token=' + access_token +
                                '&types=["time"]&key_by_type=true', verify=False)
                r = r.json()
                distpar = 5
                timepar = 5
                if list(r.keys())[0] == 'distance':
                    df_res = create_dataframe(r)

                    if max(df_res['time']) / 60 > 10:
                        result_10 = calculate_split(df_res, 10)
                    else:
                        result_10 = ['0', '0', '0']
                    if max(df_res['time']) / 60 > 20:
                        result_20 = calculate_split(df_res, 20)
                    else:
                        result_20 = ['0', '0', '0']
                    if max(df_res['time']) / 60 > 30:
                        result_30 = calculate_split(df_res, 30)
                    else:
                        result_30 = ['0', '0', '0']

                    subset = df_res[df_res['speed']<=18]

                    maxtimediff = max(subset['sumcumtimediff'])

                    maxdistdiff = max(subset['sumcumdistdiff']) 
                    
                    movingspeed = round((((distpar - maxdistdiff) / (timepar - maxtimediff)) * 3.6),2)
                    
                    timemoving = round(((timepar - maxtimediff) / 60),0)
                    
                    prctimemoving = round((((timepar - maxtimediff) / timepar) * 100),0)
                    
                    data = {
                        'Avg. Moving speed (20+)' : str(movingspeed) + ' (' + str(prctimemoving) + '%, ' + str(timemoving) + ' mins )',
            '50% Qrt Speed': str(round(min(df_res[df_res['percentilerounded']==50]['speed']),2)), 
            'Best 10 min Speed' : result_10[0] + ' @ ' + result_10[1] + ' min & ' + result_10[2] + ' km.',
            'Best 20 min Speed' : result_20[0] + ' @ ' + result_20[1] + ' min & ' + result_20[2] + ' km.',
            'Best 30 min Speed' : result_30[0] + ' @ ' + result_30[1] + ' min & ' + result_30[2] + ' km.',
            '75% Qrt Speed' : str(round(min(df_res[df_res['percentilerounded']==75]['speed']),2))
            
                            }

                return func.HttpResponse(json.dumps(data), status_code=200, mimetype='application/json')

    return func.HttpResponse("Get_Activity", status_code=r.status_code)


def get_access_token(username):
    with open('userid.json') as json_file:
                strava_tokens = json.load(json_file)
    # check if key exists for username
    if username in strava_tokens:
        # check if token is valid
        try:
            minutes_left = fn_GetMinutesLeft(strava_tokens, username)
            if minutes_left < 1:
                logging.info("18: Strava Token expired")
                response = requests.post(
                    url='https://www.strava.com/oauth/token',
                    data={
                        'client_id': 13077,
                        'client_secret': 'eff7509ab872e832466790aa0da2be7d1a40a568',
                        'grant_type': 'refresh_token',
                        'refresh_token': strava_tokens[username]['refresh_token']
                    }, verify=False)
                # Save response as json in new variable
                logging.info("19: New Strava Token")
                new_strava_tokens = response.json()
                # Save new tokens to file
                strava_tokens[username] = new_strava_tokens
                # store to local file
                with open('userid.json', 'w') as outfile:
                    json.dump(strava_tokens, outfile)
                logging.info("20: New Strava Token stored")
                access_token = strava_tokens[username]['access_token']
                return func.HttpResponse(access_token, status_code=201)
            else: # strava token is valid
                access_token = strava_tokens[username]['access_token']
                logging.info("Strava Token found")
                return func.HttpResponse(access_token, status_code=200)
        except: # strava token not found, error
            return func.HttpResponse("Get new tokens", status_code=404)
        else: #strava token not found, error
            return func.HttpResponse("User not found", status_code=404)


@app.route(route="Get_Activities")
def Get_Activities(req: func.HttpRequest) -> func.HttpResponse:
    token_str = req.headers.get('Authorization')
    if token_str:
        # send token_str to api to get username, performa a get request to api
        logging.info('15: CheckToken')
        url = "http://localhost:7072/api/CheckToken"
        headers = {'Authorization': token_str}
        r = requests.get(url, headers=headers)
        logging.info(r.status_code)
        if r.status_code == 202:
            logging.info('16: 202 terug')
            # get username from responsetext and load into json to then get the userid using that key
            username = json.loads(str(r.text))['userid']
            logging.info(username)
            # we will call our function here
            logging.info('17: get_access_token')
            access_token_response = get_access_token(username)
            stcode = access_token_response.status_code
            if stcode == 200 or stcode == 201:
                if stcode == 201:
                    logging.info('21: 201 terug')
                elif stcode == 200:
                    logging.info('22: 200 terug')
                access_token = access_token_response.get_body().decode('utf-8')
                logging.info(str(access_token))
                # get activities
                url = "https://www.strava.com/api/v3/activities"
                # Get first page of activities from Strava with all fields
                logging.info('23: get activities bij strava')
                r = requests.get(
                    url + '?access_token=' + str(access_token), verify=False)
                r = r.json()
                return func.HttpResponse(json.dumps(r), status_code=200)
            else:
                return func.HttpResponse("Get new tokens", status_code=stcode)
        else:  # checktoken failed
            return func.HttpResponse(
                "No valid authorization header was provided in the request...",
                status_code=r.status_code
            )
    return func.HttpResponse(username)


@app.route(route="Store_Tokens")
def Store_Tokens(req: func.HttpRequest) -> func.HttpResponse:
    token_str = req.params.get('state')
    code = req.params.get('code')
    if token_str:
        # send token_str to api to get username, performa a get request to api
        url = "http://localhost:7072/api/CheckToken"
        headers = {'Authorization': token_str}
        r = requests.get(url, headers=headers)
        logging.info(r.status_code)
    if r.status_code == 202:    
        username = json.loads(str(r.text))['userid']        
        with open('userid.json') as json_file:
            strava_tokens = json.load(json_file)

        response = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': 13077,
                'client_secret': 'eff7509ab872e832466790aa0da2be7d1a40a568',
                'code': code,
                'grant_type': 'authorization_code'
            }, verify=False)
        # Save json response as a variable
        logging.info(strava_tokens)
        strava_tokens[username] = response.json()
        # store to local file
        with open('userid.json', 'w') as outfile:
            json.dump(strava_tokens, outfile)

        # store json file in blob storage
        # store_to_container(strava_tokens, 'userid.json')
        # retreive json file from blob storage
        # filecontents = retreive_from_container('userid.json')
        # logging.info(filecontents)

        return func.HttpResponse(
                status_code=302,
                headers={
                    'Location': 'http://localhost:3000'
                }
            )
    else:
        return func.HttpResponse(
            "No valid authorization header was provided in the request.",
            status_code=401
        )
