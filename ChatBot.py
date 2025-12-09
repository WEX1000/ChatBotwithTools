from openai import OpenAI
from pprint import pprint
import json
import urllib.parse
import requests

with open("KEY.key") as f:
    OPENAI_KEY = f.read().strip()

client = OpenAI(
    api_key = OPENAI_KEY
)

def city_to_lat_lon(city_name):
    headers = {
        "User-Agent": "DemoAppForPythonAPICourse",
    }

    r = requests.get(f"https://nominatim.openstreetmap.org/search?city={urllib.parse.quote(city_name)}&format=json", headers=headers)

    body = r.json()
    print(body)
    exit
    lat = body[0]["lat"]
    lon = body[0]["lon"]
    return {
      "lat": lat,
      "lon": lon,
    }

def get_weather(lat, lon):
    r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={float(lat)}&longitude={float(lon)}&current=temperature_2m")
    body = r.json()
    return {
      "temperature": str(body["current"]["temperature_2m"]) +
    body["current_units"]["temperature_2m"]
    }

tools = [
    {
        "type" : "function",
        "name" : "add_two_numbers",
        "description" : "Adds two integers represented as decimal strings and returns the resoult also as a decimal string",
        "parameters" : {
            "type" : "object",
            "properties" : {
                "a" : {
                    "type" : "string",
                    "description" : "First number to add as decimal string"
                },
                "b" : {
                    "type" : "string",
                    "description" : "Second number to add as decimal string"
                }
            },
            "required" : ["a", "b"]
        }
    },
    {
        "type": "function",
        "name": "city_to_latitude_longitude",
        "description": "Gets a city name as string and returns its latitude and longitude.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name",
                }
            },
            "required": ["city"]
        }
    },
    {
        "type": "function",
        "name": "get_whether_at_latitude_longitude",
        "description": "Returns the temperature at a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "lat": {
                    "type": "string",
                    "description": "Latitude of the location",
                },
                "lon": {
                    "type": "string",
                    "description": "Longitude of the location",
                }
            },
            "required": ["lat", "lon"]
        }
    }
]

def my_add(a, b):
    a = int(a)
    b = int(b)
    return str(a + b)

chatlog = []

chatlog.append({
    "role" : "developer",
    "content" : "You are a helpful home assistant. Help the user in what they want."
})

skip_user_input = False


while True:
    if not skip_user_input:
        user_msg = input("? ")
        chatlog.append({
            "role" : "user",
            "content" : user_msg 
        })
    else:
        skip_user_input = False

    r = client.responses.create(
        model="gpt-5.1",
        input=chatlog,
        tools=tools
    )

    for output_msg in r.output:
        chatlog.append(output_msg)

        if output_msg.type == "message":
            for msg in output_msg.content:
                if msg.type == "output_text":
                    print(f"\x1b[1;33m{msg.text}\x1b[m")
                else:
                    print("UNKNOWN TYPE!", msg)
        elif output_msg.type == "function_call":
            print(f"\x1b[1;31mFunction call: {output_msg.name}\x1b[m")
            if output_msg.name == "add_two_numbers":
                args = json.loads(output_msg.arguments)
                res = my_add(args["a"], args["b"])
                chatlog.append({
                    "type" : "function_call_output",
                    "call_id" : output_msg.call_id,
                    "output" : json.dumps({
                        "resoult" : res
                    })
                })
                skip_user_input = True
            elif output_msg.name == "city_to_latitude_longitude":
                args = json.loads(output_msg.arguments)
                print(args["city"])
                res = city_to_lat_lon(args["city"])
                chatlog.append({
                    "type": "function_call_output",
                    "call_id": output_msg.call_id,
                    "output": json.dumps(res)
                })
                print(res)
                skip_user_input = True
            elif output_msg.name == "get_whether_at_latitude_longitude":
                args = json.loads(output_msg.arguments)
                res = get_weather(args["lat"], args["lon"])
                print(args["lat"], args["lon"])
                chatlog.append({
                    "type": "function_call_output",
                    "call_id": output_msg.call_id,
                    "output": json.dumps(res)
                })
                print(res)
                skip_user_input = True
            else:
                print("CHATGPT WANTED TO CALL UNKNOWN FUNCTION", output_msg)
        else:
            print("UNKNOWN OUTPUT TYPE!", output_msg)