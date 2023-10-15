import azure.functions as func
import logging
import jwt

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="Resource_API")
def Resource_API(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    #print the header of the request
    logging.info(req.headers.get('Authorization'))

    name = req.headers.get('Authorization')
    # decode name using jwt and a secret key
    decoded_name = None
    if name:
        try:
            decoded_name = jwt.decode(name, 'SFGBER345345#$%#$fefe', algorithms=['HS256'])
            userid = decoded_name.get('userid')
            logging.info(decoded_name)
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
        return func.HttpResponse(userid)
    else:
        return func.HttpResponse(
             "No valid authorization header was provided in the request.",
             status_code=401
        )
