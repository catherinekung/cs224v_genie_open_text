import bson
import re

with open(r'dump_data/yelp_data.bson','rb') as f:
    data = bson.decode_all(f.read())

def add_element(dict_input, name, location, review):
    new_dict = {location: review}
    # If the key exists, append the review to the existing list of reviews
    if name in dict_input:
        dict_input[name].append(new_dict)
    # If the key doesn't exist, create a new key-value pair
    else:
        dict_input[name] = [new_dict]

data_reviews_only = {}
count = 0
for i in range(len(data)):
    # Check that location, name, and review exist
    if ("name" in data[i]) and ("reviews" in data[i]) and ("location" in data[i]):
        count = count + 1
        location = (data[i]["location"]["city"], data[i]["location"]["address1"], data[i]["location"]["zip_code"])
        name = data[i]["name"] # restuarant name
        reviews = data[i]["reviews"] # all reviews
        name_id = (id,name)
        add_element(data_reviews_only, name, location, reviews)

def get_topic_and_resturant(user_input, dict):
    try:
        topic = re.search('about the (.+?) at', user_input).group(1)
        restuarant = user_input.partition("at ")[2]
        # print(topic)
        # print(restuarant)
    except AttributeError:
        raise Exception("Check input, topic or restuarant not extracted")
    return topic, restuarant

def get_topic_and_resturant_with_location(user_input, dict):
    try:
        topic = re.search('about the (.+?) at', user_input).group(1)
        restuarant = re.search('at (.+?) in', user_input).group(1)
        zip = user_input.partition("in ")[2]

        print(topic)
        print(restuarant)
        print(zip)
    except AttributeError:
        raise Exception("Check input, topic or restuarant not extracted")
    return topic, restuarant, zip

user_input = "Tell me about the ambiance at Carnitas Michoacan"
topic,restuarant = get_topic_and_resturant(user_input, data_reviews_only)
num_locations = len(data_reviews_only[restuarant])

location_idx = ""
location_key = ""
if num_locations > 1:
    # Ask again with zip code
    user_input = "Tell me about the ambiance at Carnitas Michoacan in 95138"
    topic, restuarant, zip = get_topic_and_resturant_with_location(user_input, data_reviews_only)

    # Get first review
    all_reviews = data_reviews_only[restuarant]
    for i in range(num_locations):
        orig_keys = all_reviews[i].keys()
        keys = list(orig_keys)
        if keys[0][2] == zip:
            location_idx = i
            location_key = keys[0]
    reviews = all_reviews[location_idx][location_key]
else:
    reviews = data_reviews_only[restuarant]

print(reviews)

