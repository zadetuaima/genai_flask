from openai import AzureOpenAI
import os
import requests
import json

client = AzureOpenAI(
    api_key = os.getenv("AZURE_KEY"),
    azure_endpoint = os.getenv("AZURE_ENDPOINT"),
    api_version = "2023-10-01-preview"
)


#inital chat input message
messages = [
    {"role":"user",
     "content":"Find the current price of etherium in GBP and return the answer as a poem"}
]


#helper function for crypto prices
#so fetches current price of crypto in a specifci currency via coingecko API

#this is API specific to whatever one you are using
def crypto_price(crypto_name, fiat_currency):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={fiat_currency}"
    response = requests.get(url)
    data = response.json()
    current_price = [coin["current_price"] for coin in data if coin["id"] == crypto_name][0]
    return f"The current price of {crypto_name} is {current_price} {fiat_currency} at the moment!"

#GPT metadata function
#This provides the GPT with metadata about a custom function, so this but is essential for initalising the GPT
functions = [
	{
		"type": "function",
		"function": {
			"name": "get_crypto_price",
			"description": "Gets prices of a cryptocurrency in a specifc currency",
			"parameters": {
				"type": "object",
				"properties": {
					"crypto_name": {
                    "type": "string",
                    "description": "the name of the crypto currency that I want to look at"
                    },
                    "fiat_currency": {
                        "type": "string",
                        "description": "The fiat currency for definding the price of crypto currency using the official currency abbreviation"
                    }
                },
                "required": ["cyrpto_name", "fiat_currency"]
			}
		}
	}
]


#This is the initial chat completion request, where it send the user message and function description to the gpt
#bascially routes all the info above to the openAI API so it can get an answer
response = client.chat.completions.create(
    model = "GPT-4",
    messages = messages,
    tools = functions,
    #auto means chatgpt decides when it wants to call this function
    tool_choice = "auto"
)

#response_message is the initial response of the GPT
response_message = response.choices[0].message
#gpt_tools determines if the GPT needs external data
gpt_tools = response.choices[0].message.tool_calls

#gpt_tools is a list
if gpt_tools: #if GPT tools is being requested...
    #so we want to set up a 'phonebook', where if we see a function name we are able to tell our code which fucntion to tool_calls
    #bit below is the 'phonebook'
    avaliable_functions = {
        "get_crypto_price": crypto_price
    }

    #this whole bit below is updated the convo history, so that the bot doesn't get confused when you keep sending it stuff
    messages.append(response_message)
    for gpt_tool in gpt_tools: #loops through each tool call requested by the GPT
        #so at this point, gpt is going to want to decide which bit of infomation they want to grab,
        #so in this case it looks up the fucntuon
        function_name = gpt_tool.function.name
        #here I'm looking up the functuon name within the 'phonebook'
        function_to_call = avaliable_functions[function_name] #Looks up the corresponding Python function in the avaliable_functions dictionary
        # need the parameters for the function
        function_parameters = json.loads(gpt_tool.function.arguments) #this contains the parameters of the function
        function_response = function_to_call(function_parameters.get("crypto_name"), function_parameters.get("fiat_currency")) #this bit then executes the function

        #this appends the tool response to the convo
        messages.append(
			{
				"tool_call_id": gpt_tool.id,
				"role": "tool",
				"name": function_name,
				"content": function_response
			}
		)

        #then this requests a follow-up response from the GPT
        second_response = client.chat.completions.create(
			model = "GPT-4",
			messages = messages
		)
        print(second_response.choices[0].message.content)

#and if the GPT doesn't need any tools, i.e. if the initial question doesnt relate to crypto in this case it will just print a repsonse as normal
else:
    print(response.choices[0].message.content)
