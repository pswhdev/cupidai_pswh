from rest_framework.views import APIView
from rest_framework.response import Response
from requests import request
from .serializers import GptSerializer, GeolocationSerializer
from rest_framework import status
from django.conf import settings
import json
from openai import OpenAI
from django.http import StreamingHttpResponse

GPT_MODEL = 'gpt-3.5-turbo'
GPT_URL = 'https://api.openai.com/v1/chat/completions'

GOOGLE_PLACES_URL = 'https://places.googleapis.com/v1/places:searchText' 

def stream_response(completion_stream):
    """ Read chunks from stream """ 
    for chunk in completion_stream:
        content = chunk.choices[0].delta.content
        if content is None:
            return
        yield content

# class AskGptView(APIView):

#     def post(self, req):

#         req_data = GptSerializer(data=req.data)

#         # Check if request is valid
#         if req_data.is_valid():

#             # Do the request to open API
#             messages = [{"role": "user", "content": req_data.validated_data.get('message')}]

#             # Create the OpenAi client
#             client = OpenAI()

#             # Request GPT stream
#             res = client.chat.completions.create(model=GPT_MODEL, messages=messages, stream=True, max_tokens=500)

#             print(res)

#             # Return a streaming response
#             return StreamingHttpResponse(stream_response(res), content_type='text/plain')

#         else:
#             # Return 400 and validation errors
#             return Response(req_data.errors, status=status.HTTP_400_BAD_REQUEST)



class AskGptView(APIView):
    
    def post(self, req):
        openai_api_key = settings.OPENAI_API_KEY

        req_data = GptSerializer(data=req.data)

        # Check if request is valid
        if req_data.is_valid():

            # Do the request to open API
            data = {
                'model': GPT_MODEL,
                "messages": [{"role": "user", "content": req_data.validated_data.get('message')}]
            }
            res = request("POST", GPT_URL, 
                          headers={'Authorization': 'Bearer ' + openai_api_key}, 
                          json=data, timeout=10)

            # Parse GPT response
            parsed_json = json.loads(res.text)
            choices = parsed_json['choices']

            # Access GPT message
            gpt_message = choices[0]['message']['content']


            # Return GPT message
            return Response({'message': gpt_message})
        else:
            # Return 400 and validation errors
            return Response(req_data.errors, status=status.HTTP_400_BAD_REQUEST)


class GeolocationView(APIView):
    def post(self, req):

        places_api_key = settings.PLACES_API_KEY

        req_data = GeolocationSerializer(data=req.data)

        # Check if request is valid
        if req_data.is_valid():

            # Do the request to Google Places API
            data = {
                'textQuery': req_data.validated_data.get('text'),
                'locationBias': {
                    'circle': {
                        'center': { 'latitude': req_data.validated_data.get('lat'), 'longitude': req_data.validated_data.get('lng') },
                        'radius': 1000.0,
                    },
                },
            }

            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": places_api_key,
                "X-Goog-FieldMask": "*",
            }

            res = request("POST", GOOGLE_PLACES_URL, headers=headers, json=data, timeout=10)

            # Parse the response
            parsed_json = json.loads(res.text)
            print(parsed_json)


            return Response(parsed_json)

        else:  
             # Return 400 and validation errors
            return Response(req_data.errors, status=status.HTTP_400_BAD_REQUEST)
        
