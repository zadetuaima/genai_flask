from openai import AzureOpenAI
import os
import requests
import json

client = AzureOpenAI(
	api_key = os.getenv("AZURE_KEY"),
	azure_endpoint = os.getenv("AZURE_ENDPOINT"),
	api_version = "2023-10-01-preview"
)

messages = [
	{"role": "system", "content": "Respond to everything as a short poem"},
]

def crypto_price(crypto_name, fiat_currency):
	url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={fiat_currency}"
	print(url)
	response = requests.get(url)
	data = response.json()
	# my_coin is the selected dictionary with all crypto data for selected crypto
	current_price = [coin['current_price'] for coin in data if coin['id'] == crypto_name][0]
	return f"The current price of {crypto_name} is {current_price} {fiat_currency}"

functions = [
	{
		"type": "function",
		"function": {
			"name": "get_crypto_price",
			"description": "Gets prices of crypto currency in a specified global currency",
			"parameters": {
				# lettings chat-gpt know that it's getting
				# key-value pairs
				"type": "object",
				"properties": {
					"crypto_name": {
						"type": "string",
						"description": "The name of the crypto currency that I want to look up"
					},
					"fiat_currency": {
						"type": "string",
						"description": "The fiat currency for defining the price of crypto currency. Use the official abbreviation"
					}
				},
				"required": ["crypto_name", "fiat_currency"]
			}
		}
	}
]



def ask_question(user_question):
	# we're building a converation, and saying every message
	# from the user
	messages.append({"role": "user", "content": user_question})

	response = client.chat.completions.create(
		model = "GPT-4",
		messages = messages,
		tools = functions,
		# auto means chat-gpt decides when it needs to use external functions
		tool_choice = "auto"
	)

	response_message = response.choices[0].message
	# if chat-gpt doesn't need help, this will be None, otherwise there will be stuff
	gpt_tools = response.choices[0].message.tool_calls

	# if gpt_tools is not None
	# gpt_tools is a list!
	if gpt_tools:

		# set up a 'phonebook', if we see a function name, we need to tell our code
		# which function to call
		available_functions = {
			"get_crypto_price": crypto_price
		}

		messages.append(response_message)
		for gpt_tool in gpt_tools:
			# figure out which friend to call
			function_name = gpt_tool.function.name
			# looking up my function name in my 'phonebook'
			function_to_call = available_functions[function_name]
			# need the parameters for the function
			function_parameters = json.loads(gpt_tool.function.arguments)
			function_response = function_to_call(function_parameters.get('crypto_name'), function_parameters.get('fiat_currency'))
			messages.append(
				{
					"tool_call_id": gpt_tool.id,
					"role": "tool",
					"name": function_name,
					"content": function_response
				}
			)
			second_response = client.chat.completions.create(
				model = "GPT-4",
				messages=messages
			)
			# this response happens if you use the crypto function
			return second_response.choices[0].message.content

	else:
		# this is the chatbot response if no external function is used
		return response.choices[0].message.content
