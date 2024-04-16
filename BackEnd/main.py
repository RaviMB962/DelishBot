from fastapi import FastAPI, BackgroundTasks
from fastapi import Request
from fastapi.responses import JSONResponse
import time
from threading import Thread

import db_helper
import generic_helper


app = FastAPI()

inprogress_orders = {}

ORDER_TIMEOUT = 60*2 # 2 min * 60 seconds = Total 120 seconds

# Dictionary to store the last activity timestamp for each order
order_activity = {}

@app.post("/")
async def handle_request(request: Request):
    # Retrive the JSON data from the request
    payload = await  request.json()

    # Extract the necessary info from the payload
    # based on the structure of WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id  = generic_helper.extract_session_id(output_contexts[0]["name"])

    # Update the last activity time stamp for the order    
    order_activity[session_id] = time.time()

    intent_handler_dict = {
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order,
        'timeout.order':close_order,
        'cancel_order - contex: ongoing-order': cancel_order
    }


    return intent_handler_dict[intent](parameters, session_id)


def cancel_order(parameters: dict, session_id: str):
    # Your logic to cancel the order goes here
    #fulfillment_text = "Your order has been successfully canceled."
    #return JSONResponse(content={"fulfillmentText": fulfillment_text})

    if session_id in inprogress_orders:
        del inprogress_orders[session_id]
        fulfillment_text = "Your order has been successfully canceled."
    else:
        fulfillment_text = "No active order found for the current session. Please start a new order."
    return JSONResponse(content={"fulfillmentText": fulfillment_text})


# Function to periodically check for inactive orders and close them
def check_inactive_orders():
    while True:
        current_time = time.time()
        for session_id, last_activity_time in order_activity.items():
            if current_time - last_activity_time > ORDER_TIMEOUT:
                #print("Order timed out for session:", session_id)
                #close which the order more than 2 mi in active
                close_order(session_id)
                #automatic_reply(session_id)
            time.sleep(10) # Check every 30 sec for inactive order
'''
def automatic_reply(session_id):
    fulfillment_text = "Your order has been automatically closed due to inactivity. " \
                       "Please place a new order if you wish to proceed."
    #print("Automatic reply sent for session(auto reply):", session_id)                   
    return JSONResponse(content={"fulfillmentText": fulfillment_text})'''


# Start a background task to check for inactive orders
check_thread = Thread(target=check_inactive_orders)
check_thread.daemon = True
check_thread.start()


def close_order(session_id):
    # Handle closing of the order (e.g., remove from database)
    if session_id in inprogress_orders:
        del inprogress_orders[session_id]
        fulfillment_text = "Your order has been closed due to inactivity. Please place a new order if you wish to proceed."
        #print("Order closed for session:", session_id)
    else:
        fulfillment_text = "No active order found for the current session. Please start a new order."
        #print("No active order found for session:", session_id)
    return JSONResponse(content={"fulfillmentText": fulfillment_text})
        
    

     

def remove_from_order(parameters: dict , session_id:str):
    
    # inprogress_orders = {
    #          "session_id_1": {'vada pav": 3, "pizza":2, "mango lassi":1},
    #           "session_id_2": {'masala dosa": 4}
    # }
    # step 1: locate the session id record: { "session_id_1": {'vada pav": 3, "pizza":2, "mango lassi":1}}
    # step2 : get the value from dict: {'vada pav": 3, "mango lassi":1}
    # step 3: remove the food item . request : ["vada pav", "rava dosa"]

    # removed vad pav from order. Rava dosa not found in your order


    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! can you please a new order."
        })
    current_order = inprogress_orders[session_id]
    food_items = parameters["food-item"]

    removed_items = []

    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) >0:
        fulfillment_text = f"Removed {', '.join(removed_items)} from your order"

    if len(no_such_items)>0:
        fulfillment_text = f"Your current order does not have {', '.join(no_such_items)}."

    if len(current_order.keys()) ==0:
        fulfillment_text += " Your order is empty!"
    else:
        #remaining items 
        order_str = generic_helper.get_string_from_food_dictionary(current_order)
        fulfillment_text += f"Here is what is left in your order: {order_str}"

    return JSONResponse( content = {
        "fulfillmentText": fulfillment_text
    })



def add_to_order(parameters:dict, session_id:str):
    food_items = parameters["food-item"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Can you please specify food items quantities"
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_string_from_food_dictionary(inprogress_orders[session_id])

        fulfillment_text = f"So for you have: {order_str} .Do you want anything else?"

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

def complete_order(parameters: dict, session_id:str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having trouble finding your order. Sorry! can you place a new order please!!!"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id ==-1:
            fulfillment_text = "Sorry, I couldn't process your order due to backend error."\
                                "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order." \
                                f" Here is your order id #{order_id}."\
                                f" Your order total is {order_total} which you can pay at the time of delivary!"

        #once order is placed we need to remove order details from inprogress_orders list
        del inprogress_orders[session_id]


    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def save_to_db(order:dict):
    #order = {{"pizza": 2, "Mosala Dosa": 1}
    # as procedural function inside sql db is taking one food item for one time, so we need to iterate here

    next_order_id = db_helper.get_next_order_id()

    for  food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id


def track_order(parameters: dict, session_id: str):

    order_id = int(parameters['order_id'])
    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })
