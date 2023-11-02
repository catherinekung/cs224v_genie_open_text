import bson
import re
class Yelp_Data():
    def __init__(self):

        with open(r'C:\Users\angie\Documents\2.) Stanford\Stanford2023\STANFORD FALL 2023\CS224V\Project\cs224v_genie_open_text\pipelines\final_project\dump_data\yelp_data.bson', 'rb') as f:
            data = bson.decode_all(f.read())
        self.data_reviews_only = {}
        for i in range(len(data)):
            # Check that location, name, and review exist
            if ("name" in data[i]) and ("reviews" in data[i]) and ("location" in data[i]):
                location = (data[i]["location"]["city"], data[i]["location"]["address1"], data[i]["location"]["zip_code"])
                name = data[i]["name"] # restaurant name
                reviews = data[i]["reviews"] # all reviews
                self.add_element(self.data_reviews_only, name, location, reviews)

    def add_element(self, dict_input, name, location, review):
        new_dict = {location: review}
        # If the key exists, append the review to the existing list of reviews
        if name in dict_input:
            dict_input[name].append(new_dict)
        # If the key doesn't exist, create a new key-value pair
        else:
            dict_input[name] = [new_dict]

    def get_topic_and_restaurant(self, user_input):
        try:
            topic = re.search('about the (.+?) at', user_input).group(1)
            restaurant = user_input.partition("at ")[2]
        except AttributeError:
            raise Exception("Check input, topic or restaurant not extracted")
        return topic, restaurant

    def get_topic_and_restaurant_with_location(self, user_input):
        try:
            topic = re.search('about the (.+?) at', user_input).group(1)
            try:
                zip = user_input.partition("in ")[2]
                restaurant = re.search('at (.+?) in', user_input).group(1)
            except:
                zip = None
                restaurant = user_input.partition("at ")[2]
            print("\tTopic: ", topic)
            print("\tRestaurant: ", restaurant)
            print("\tZip Code: ",zip)
        except AttributeError:
            raise Exception("Check input, topic or restaurant not extracted")
        return topic, restaurant, zip

    def fetch_reviews(self, user_input):
        topic, restaurant = self.get_topic_and_restaurant(user_input)
        num_locations = len(self.data_reviews_only[restaurant])
        location_idx = ""
        location_key = ""
        if num_locations >= 1:
            topic, restaurant, zip = self.get_topic_and_restaurant_with_location(user_input)

            # Get last location review
            all_reviews = self.data_reviews_only[restaurant]
            for i in range(num_locations):
                orig_keys = all_reviews[i].keys()
                keys = list(orig_keys)
                if keys[0][2] == zip:
                    location_idx = i
                    location_key = keys[0]
                if zip is None:
                    location_idx = i
                    location_key = keys[0]
            reviews = all_reviews[location_idx][location_key]
        else:
            reviews = self.data_reviews_only[restaurant]
        print("\tReview from:", location_key)
        return reviews
        # print("\tReviews: ", reviews)

if __name__ == "__main__":
    print("Hello, World!")
    yelp_reviews = Yelp_Data()
    user_input = "Tell me about the ambiance at The Funny Farm"
    reviews = yelp_reviews.fetch_reviews(user_input)
    for i in reviews:
        print(i)


