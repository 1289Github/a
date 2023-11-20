from flask import Flask, render_template, request, jsonify
import openai
import config
import json
import sys
import random
import re
from datetime import datetime


app = Flask(__name__, static_url_path='/static')

# Set your Azure OpenAI API key here
openai.api_type = config.api_type
openai.api_base = config.api_base
openai.api_version = config.api_version
openai.api_key = config.api_key

with open('menu.json', 'r') as menu_file:
    menu = json.load(menu_file)

# Initialize an order database (JSON file)
order_database_file = 'order_database.json'


instruction = """
You are Virtual AI friendly food order Assistant for Spice Delight Restaurant and and dont reply anything other than food related queries. Your goal is to assist customers in placing their food orders for the restaurant accurately and efficiently. Here's how you should operate and follow as per the customer inputs:

1. Greeting and Introduction:
    - Welcome the customer and ask for their name in a friendly manner.

2. Taking Orders:
    - After the customer provides their name, firstly inform them about the ongoing offers or combo offers available in the menu.
    - Present only the available menu options and items, special offers, and suggest additional items.
    - Prompt for item selection and quantity, only if the customer chooses induvidual items from the menu.
    - If the customer choose combo offers, ask how many such combos do you want or are you sure of one combo?.

3. Order Confirmation:
    - Summarize the order for confirmation.
    - Ask if the customer wants to make any changes.
    - List items with names, quantities, and customizations.
    - Confirm the entire order.
 
4. Delivery or Pickup Information:
    - Always Request delivery or pickup details.
    - For delivery, ask for the customer's address.
    - For pickup, confirm the pickup location at 123 Main Street, Dallas, USA.
    - Provide an estimated time of 30 min either for delivery or pickup.

5. Payment Method:
    - Always Tell the customer that the payment link will be sent to your registered mobile number.

6. Order Summary & Final Greetings:**DO NOT SKIP THIS STEP AT THE END**
    - Always make sure to Conclude or end the conversation with an Order Summary that includes Customer Name:, Items:, Total price:, Payment Mode:, Pickup/Delivery: and thank the customer for choosing Hungry Haven Cafe and assure them of a delicious meal.

Follow these steps efficiently and diligently.
"""


# Initialize the conversation with a system message
conversation = [
    {"role": "system", "content": f"""{instruction}{menu}"""},
    {"role": "system", "content": f"""Always provide the Order Summary at the end right after the completion of payment that includes - Customer Name: \n Items with Quantities \n Total Price of the Order: \n Payment Mode: \n Phone Number(if specified) \n delivery or pickup"""}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    conversation.append({"role": "user", "content": user_input})
   
    response = openai.ChatCompletion.create(
        engine="foodorderopenai",
        messages=conversation,
        temperature=0.5,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    reply = response.choices[0].message["content"]
    conversation.append({"role": "user", "content": reply})

    order_id = len(open(order_database_file).readlines()) + 1

    # Save the order to the database
    order_summary = {
        "OrderID": order_id,
        "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "OrderSummary":[]
    
    }
    lines = reply.split('\n')
    for line in lines:
        if "- "  in line:
            item = line.replace("- ", "").strip()
            order_summary["OrderSummary"].append(item)
        elif ": "  in line:
            item = line.replace("- ", "").strip()
            order_summary["OrderSummary"].append(item)

    # Save the order summary to the order_database.json file
    with open(order_database_file, 'a') as order_file:
            order_json = json.dumps(order_summary, indent=4)
            order_file.write(order_json)
            order_file.write('\n')

    
    reply = reply.replace('\n', '<br>')
    response_json = {'reply': reply, 'OrderID': order_id}
    return jsonify(response_json)

if __name__ == '__main__':
    app.run(debug=True)
    sys.exit()
