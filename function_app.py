import azure.functions as func
import logging
import jwt
import json
import requests
from bp_azure_blob import store_to_container, retreive_from_container
from bp_token_functions import fn_GetMinutesLeft
import datetime
import time

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route('User', methods=['GET'])
def get_users(req: func.HttpRequest) -> func.HttpResponse:
    # Handle GET request for /api/users
    token_str = req.headers.get('Authorization')    
    if token_str:
        try:
            decoded_name = jwt.decode(token_str, 'SFGBER345345#$%#$fefe', algorithms=['HS256'])
            username = decoded_name.get('userid')
            # create json file with userid
            #if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(decoded_name['exp']):
            #    return func.HttpResponse(json.dumps({'error': 'token expired'}), status_code=401)
            # Make Strava auth API call with your 
            # client_code, client_secret and code
            with open('userid.json') as json_file:
                strava_tokens = json.load(json_file)
            
            # check if key exists for username
            if username in strava_tokens:
                # add 4 seconds delay
                time.sleep(4)
                return func.HttpResponse("User found", status_code=202)
            else:
                return func.HttpResponse("User not found", status_code=404) #

        except jwt.ExpiredSignatureError:
            return func.HttpResponse(
                "The authorization token has expired.",
                status_code=401
            )
        except jwt.InvalidTokenError:
            return func.HttpResponse(
                "The authorization token is invalid.",
                status_code=401
            )        
    else:
        return func.HttpResponse(
             "No valid authorization header was provided in the request.",
             status_code=401
        )
    return func.HttpResponse(username)


@app.route(route="Get_Activities")
def Get_Activities(req: func.HttpRequest) -> func.HttpResponse:
        token_str = req.headers.get('Authorization')    
        if token_str:
            try:
                decoded_name = jwt.decode(token_str, 'SFGBER345345#$%#$fefe', algorithms=['HS256'])
                username = decoded_name.get('userid')
                with open('userid.json') as json_file:
                    strava_tokens = json.load(json_file)
                # check if key exists for username
                if username in strava_tokens:
                    # check if token is valid
                    try:
                        minutes_left = fn_GetMinutesLeft(strava_tokens, username)
                        if minutes_left < 1:
                            logging.info("Strava Token expired")                        
                            response = requests.post(
                                url = 'https://www.strava.com/oauth/token',
                                data = {
                                        'client_id': 13077,
                                        'client_secret': 'eff7509ab872e832466790aa0da2be7d1a40a568',
                                        'grant_type': 'refresh_token',
                                        'refresh_token': strava_tokens[username]['refresh_token']
                                        }
                            , verify=False)
                            # Save response as json in new variable
                            new_strava_tokens = response.json()
                            # Save new tokens to file
                            strava_tokens[username] = new_strava_tokens
                            # store to local file
                            with open('userid.json', 'w') as outfile:
                                json.dump(strava_tokens, outfile)
                            return func.HttpResponse("Strava Token expired", status_code=201)
                        else:
                            access_token = strava_tokens[username]['access_token']
                            # get activities
                            url = "https://www.strava.com/api/v3/activities"
                            # Get first page of activities from Strava with all fields
                            r = requests.get(url + '?access_token=' + access_token, verify=False)
                            r = r.json()
                            
                            return func.HttpResponse(json.dumps(r), status_code=200)
                    except:
                            return func.HttpResponse("Get new tokens", status_code=404)
                else:
                    return func.HttpResponse("User not found", status_code=404)

            except jwt.ExpiredSignatureError:
                return func.HttpResponse(
                    "The authorization token has expired.",
                    status_code=401
                )
            except jwt.InvalidTokenError:
                return func.HttpResponse(
                    "The authorization token is invalid.",
                    status_code=401
                )        
        else:
            return func.HttpResponse(
                "No valid authorization header was provided in the request.",
                status_code=401
            )
        return func.HttpResponse(username)

@app.route(route="Store_Tokens")
def Store_Tokens(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    #print the header of the request
    
    logging.info( req.params.get('state'))
    token =  req.params.get('state')
    code =  req.params.get('code')
    # decode name using jwt and a secret key
    decoded_name = None
    if token:
        try:
            decoded_name = jwt.decode(token, 'SFGBER345345#$%#$fefe', algorithms=['HS256'])
            username = decoded_name.get('userid')
            
            with open('userid.json') as json_file:
                strava_tokens = json.load(json_file)
            
            response = requests.post(
                                url = 'https://www.strava.com/oauth/token',
                                data = {
                                        'client_id': 13077,
                                        'client_secret': 'eff7509ab872e832466790aa0da2be7d1a40a568',
                                        'code': code,
                                        'grant_type': 'authorization_code'
                                        }
                            ,verify=False)
            #Save json response as a variable
            logging.info(strava_tokens)
            strava_tokens[username] = response.json()
            # store to local file
            with open('userid.json', 'w') as outfile:
                json.dump(strava_tokens, outfile)

            # store json file in blob storage
            # store_to_container(strava_tokens, 'userid.json')
            # retreive json file from blob storage            
            #filecontents = retreive_from_container('userid.json')
            #logging.info(filecontents)            
            
        except jwt.ExpiredSignatureError:
            return func.HttpResponse(
                "The authorization token has expired.",
                status_code=401
            )
        except jwt.InvalidTokenError:
            return func.HttpResponse(
                "The authorization token is invalid.",
                status_code=401
            )        

    if decoded_name:
            # Redirect to a page
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
