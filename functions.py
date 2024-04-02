import json 
import random
import datetime
import uuid
import numpy as np
import pickle
import pymongo
import nltk
from keras.models import load_model
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

words = pickle.load(open("words.pkl", "rb"))
classes = pickle.load(open("classes.pkl", "rb"))
orders = []
order_id = ""
seat_count = 50
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["restaurant"]
menu_collection = db["menu"]
feedback_collection = db["feedback"]
bookings_collection = db["bookings"]
order_collection = db["orders"]
with open("dataset.json") as file:
    data = json.load(file)
intents = json.loads(open("dataset.json").read())

model = load_model("chatbot_model.h5")

def book_table():
    global seat_count
    seat_count -= 1
    booking_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    booking_time = now.strftime("%y-%m-%d %H:%M:%S")
    booking_doc = {"booking_id ":  booking_id, "booking_time":  booking_time}
    bookings_collection.insert_one(booking_doc)
    return booking_id

def vegan_menu():
    query = {"vegan": "Y"}
    vegan_doc = menu_collection.find(query)
    if vegan_doc.count() > 0: 
        response = "vegan options are: "
        for x in vegan_doc:
            response = response + str(x.get("item")) + " for Rs. " + str(x.get("cost")) + "; " 
        response = response[:-2] #remove the last ;
    else:
        response = "Sorry no Vegan options are available"
    return response

def veg_menu():
    query = {"veg": "Y"}
    vegan_doc = menu_collection.find(query)
    print(vegan_doc)
    if vegan_doc.count() > 0:
        response = "Vegetarian options are: "
        for x in vegan_doc:
            response = response + str(x.get("item")) + " for Rs. " + str(x.get("cost")) + "; "
        response = response[:-2] # to remove the last ;
    else:
        response = "Sorry no vegetarian options are available"
    return response


def offers():
    all_offers = menu_collection.distinct('offer')
    if len(all_offers)>0:
        response = "The SPECIAL OFFERS are: "
        for ofr in all_offers:
            docs = menu_collection.find({"offer": ofr})
            response = response + ' ' + ofr.upper() + " On: "
            for x in docs:
                response = response + str(x.get("item")) + " - Rs. " + str(x.get("cost")) + "; "
            response = response[:-2] # to remove the last ;
    else:
        response = "Sorry there are no offers available now."
    return response


def suggest():
    response = "suggestion function"
    day = datetime.datetime.now()
    day = day.strftime("%A")
    if day == "Monday":
        response = "Chef recommends: Paneer Grilled Roll, Jade Chicken"
    elif day == "Tuesday":
        response = "Chef recommends: Tofu Cutlet, Chicken A La King"

    elif day == "Wednesday":
        response = "Chef recommends: Mexican Stuffed Bhetki Fish, Crispy corn"

    elif day == "Thursday":
        response = "Chef recommends: Mushroom Pepper Skewers, Chicken cheese balls"

    elif day == "Friday":
        response = "Chef recommends: Veggie Steak, White Sauce Veggie Extravaganza"

    elif day == "Saturday":
        response = "Chef recommends: Tofu Cutlet, Veggie Steak"

    elif day == "Sunday":
        response = "Chef recommends: Chicken Cheese Balls, Butter Garlic Jumbo Prawn"
    return response

def recipe_enquiry(message):
    all_foods = menu_collection.distinct('item')
    response = ""
    for food in all_foods:
        query = {"item": food}
        food_doc = menu_collection.find(query)[0]
        if food.lower() in message.lower():
            response = food_doc.get("about")
            break
    if "" == response:
        response = "Sorry please try again with exact spelling of the food item!"
    return response


def record_feedback(message, type):
    feedback_doc = {"feedback_string": message, "type": type}
    feedback_collection.insert_one(feedback_doc)

def create_order():
    order_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    order_time = now.strftime("%y-%m-%d %H:%M:%S")
    order_doc = {"_id": order_id, "order_items": {}}
    result = order_collection.insert_one(order_doc)
    if result.inserted_id:
        return order_id
    else: 
        return "order not created"
    
def is_item_in_menu(item_name):
    query = {"item": {"$regex": f"^{item_name}$", "$options": "i"}}
    result = menu_collection.find_one(query)
    if result:
        return True
    else:
        return False

def remove_item(msg):
    # Remove the "remove" keyword and split the command into item name and quantity
    parts = msg.split()[1:]
    item_name = parts[0]

    order = order_collection.find_one({"_id": order_id})

    if order:
        order_items = order.get("order_items", {})

        # Check if the item exists in the order
        if item_name in order_items:
            del order_items[item_name]  # Remove the item from the order

            result = order_collection.update_one(
                {"_id": order_id},
                {"$set": {"order_items": order_items}}
            )

            if result.modified_count == 1:
                return f"{item_name} removed from order"
            else:
                return "Failed to remove item from order"
        else:
            return f"{item_name} is not in the order"
    else:
        return "Order not found"


def add_item(msg):
    # Remove the "add" keyword and split the command into item name and quantity
    parts = msg.split()[1:]
    if parts[-1].isdigit():
        quantity = int(parts[-1])
        item_name = " ".join(parts[:-1])  
    else:
        quantity = 1
        item_name = " ".join(parts)

    if is_item_in_menu(item_name):
        order = order_collection.find_one({"_id": order_id})

        if not order:
            order = {"_id": order_id, "order_items": {}}

        order_items = order.get("order_items", {})

        # Check if the item already exists in the order items
        if item_name in order_items:
            # Increment the quantity of the existing item
            order_items[item_name] += quantity
        else:
            # Add a new entry for the item with the specified quantity
            order_items[item_name] = quantity

        result = order_collection.update_one(
                {"_id": order_id},
                {"$set": {"order_items": order_items}},
                upsert=True  # Create the document if it doesn't exist
        )

        if result.modified_count == 1:
            print(result)
            response = item_name + " added to your order"
            
        else:
            print(result)
            response = "cound not add items"
    else:
        response = "no item name "+ item_name +", please enter a name availabe in out menu"
    return response




def get_specific_response(tag):
    response = "did not go there"
    for intent in intents['intents']:
        if intent['tag'] == tag:
            responses = intent['responses']
            if responses == "":
                response = "something went wrong!"
                
            else: 
                response = random.choice(responses)

    # response = random.choice(responses)
    return response

def show_order():
    order = order_collection.find_one({"_id": order_id})

    if order:
        order_items = order.get("order_items", {})
        bill_details = []

        total_amount = 0

        for item_name, quantity in order_items.items():
            items_details = menu_collection.find_one({"item": item_name})

            if items_details:
                item_cost = items_details.get("cost", 0)
                item_total_cost = item_cost * quantity

                bill_details.append({
                    "item": item_name,
                    "quantity": quantity,
                    "cost_per_item": item_cost,
                    "total_cost": item_total_cost
                })
                total_amount += item_total_cost 
        
        bill_details.append({"total_amount": total_amount})
        print(bill_details)
        return bill_details
    else:
        return "Order Not Found"


def show_menu(id):
    if(id == 1):
        menus = "please select from starters, main_course, drinks, snacks"
        return menus
    elif(id == 2):
        menu_items = menu_collection.find({'category': 'starters'}, {'item': 1, 'cost': 1})
        menu_list = [{'item': item['item'], 'price': item['cost']} for item in menu_items]
        print(menu_list)
        return menu_list
    elif(id == 3):
        menu_items = menu_collection.find({'category': 'main_course'}, {'item': 1, 'cost': 1})
        menu_list = [{'item': item['item'], 'price': item['cost']} for item in menu_items]
        print(menu_list)
        return menu_list
    elif(id == 4):
        menu_items = menu_collection.find({'category': 'snacks'}, {'item': 1, 'cost': 1})
        menu_list = [{'item': item['item'], 'price': item['cost']} for item in menu_items]
        print(menu_list)
        return menu_list
    elif(id == 5):
        menu_items = menu_collection.find({'category': 'drinks'}, {'item': 1, 'cost': 1})
        menu_list = [{'item': item['item'], 'price': item['cost']} for item in menu_items]
        print(menu_list)
        return menu_list
    else: 
        err_message = "please choose from menu, drinks"
        return err_message




def get_random_response(msg):
    tag = predict_class(msg, model)
    list_of_intents = intents["intents"]
    for i in list_of_intents:
        if i["tag"] == tag[0]["intent"]:
            result = random.choice(i["responses"])
            break
        else: 
            result = "something went wrong in [grr] function"
            # result = tag[0]["intent"]
    return result
    

# chat functionalities
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    if sentence_words ==  "":
        print("sentence words empty")
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
    return np.array(bag)


def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def getResponse(msg, model):
    global seat_count, order_id
    tag = predict_class(msg, model)
    response = ""
    if tag != "":
        if tag[0]["intent"] == "book_table":
            if seat_count > 0:
                booking_id = book_table()
                response = "Your table has been booked successfully. please show this Booking ID at the counter: "+ str( booking_id )
            else: 
                response = "Sorry we are sold out!"
        elif tag[0]["intent"] == "available_tables":
            response = "There are " + str(seat_count) + " table(s) available at the moment."

        elif tag[0]["intent"] == "veg_enquiry":
            response = veg_menu()

        elif tag[0]["intent"] == "vegan_enquiry":
            response = vegan_menu()

        elif tag[0]["intent"] == "offers":
            response = offers()

        elif tag[0]["intent"] == "suggest":
            response = suggest()

        elif tag[0]["intent"] == "recipe_enquiry":
            response = recipe_enquiry(msg)

        elif tag[0]["intent"] == "menu":
            response = show_menu(1)

        elif tag[0]["intent"] == "starters":
            response = show_menu(2)

        elif tag[0]["intent"] == "main_course":
            response = show_menu(3)

        elif tag[0]["intent"] == "snacks":
            response = show_menu(4)

        elif tag[0]["intent"] == "drinks":
            response = show_menu(5)

        elif tag[0]["intent"] == "take_order":
            if order_id == "":
                order_id = create_order()
                response = "your order has been created with order_id: " + str(order_id) + "you can add and remove items and then confirm your order"
            else: 
                response = "your order has been created with order_id: " + str(order_id) + "you can add and remove items and then confirm your order "
        
        elif tag[0]["intent"] == "add":
            
            if order_id == "":
                order_id = create_order()
                response = add_item(msg)
            else:
                response = add_item(msg)

        elif tag[0]["intent"] == "remove":
            
            if order_id == "":
                order_id = create_order()
                response = remove_item(msg)
            else:
                response = remove_item(msg)

        elif tag[0]["intent"] == "show_order": 
            if order_id == "":
                response = "you havent ordered anything yet!"
            else:
                response = show_order()





        elif tag[0]["intent"] == "positive_feedback":
            record_feedback(msg, "positive")
            response = "Thank you so much for your valuable feedback. We look forward to serving you again!"

        elif "negative_feedback" == tag[0]["intent"]:
            record_feedback(msg, "negative")
            response = "Thank you so much for your valuable feedback. We deeply regret the inconvenience. We have " \
                       "forwarded your concerns to the authority and hope to satisfy you better the next time! "
        # for other intents with pre-defined responses that can be pulled from dataset
        else:
            response = get_random_response(msg)
            # response = get_specific_response(tag)
    else:
        response = "Sorry! I didn't get it, please try to be more precise."
    return response
