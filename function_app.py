import azure.functions as func
import logging
import jwt
import json
import requests
from bp_azure_blob import store_to_container, retreive_from_container
from bp_token_functions import fn_GetMinutesLeft
import datetime

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
            if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(decoded_name['exp']):
                return func.HttpResponse(json.dumps({'error': 'token expired'}), status_code=401)
            # Make Strava auth API call with your 
            # client_code, client_secret and code
            with open('userid.json') as json_file:
                strava_tokens = json.load(json_file)
            
            # check if key exists for username
            if username in strava_tokens:
                return func.HttpResponse("User found", status_code=200)
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

@app.route(route="Resource_API")
def Resource_API(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    #print the header of the request
    
    logging.info(req.headers.get('state'))
    logging.info( req.params.get('state'))
    name =  req.params.get('state')
    code =  req.params.get('code')
    # decode name using jwt and a secret key
    decoded_name = None
    if name:
        try:
            decoded_name = jwt.decode(name, 'SFGBER345345#$%#$fefe', algorithms=['HS256'])
            username = decoded_name.get('userid')
            # create json file with userid
            
            # Make Strava auth API call with your 
            # client_code, client_secret and code
            with open('userid.json') as json_file:
                strava_tokens = json.load(json_file)

            minutes_left = fn_GetMinutesLeft(strava_tokens, username)
            logging.info(minutes_left)
            '''
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
            # Save tokens to a stringvariable
            #strava_tokens = json.dumps(strava_tokens)
                       
            logging.info(strava_tokens)

            # json_data = json.dumps({ username : strava_tokens })
            # store to local file
            with open('userid.json', 'w') as outfile:
                json.dump(strava_tokens, outfile)

            # store json file in blob storage
            # store_to_container(strava_tokens, 'userid.json')
            # retreive json file from blob storage
            
            #filecontents = retreive_from_container('userid.json')
            #logging.info(filecontents)
            logging.info(decoded_name)
            '''
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
        return func.HttpResponse(str(minutes_left))
    else:
        return func.HttpResponse(
             "No valid authorization header was provided in the request.",
             status_code=401
        )
