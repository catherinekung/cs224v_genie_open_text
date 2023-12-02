import bson
import re
from collections import defaultdict
import csv


class Yelp_Data():
    # just return data_reviews_only

    def __init__(self, file_path):
        self.data_reviews_only = self.get_database(file_path)
        self.load_test_restaurant()

    def load_test_restaurant(self):
        with open(r"pipelines/final_project/dump_data/test_restaurant_reviews.csv") as file:
            reviews = []
            reader = csv.reader(file)
            for r in reader:
                reviews.append(r[0])

        self.data_reviews_only["Test Restaurant"] = [{"address": "1234 Crying", "city": "Hell", "reviews": reviews}]

    def get_database(self, file_path):
        with open(file_path, 'rb') as f:
            data = bson.decode_all(f.read())
        data_reviews_only = {}
        restaurants_ratings = defaultdict(list)
        for i in range(len(data)):
            # Check that location, name, and review exist
            if ("name" in data[i]) and ("reviews" in data[i]) and ("location" in data[i]):
                location = data[i]["location"]
                name = data[i]["name"] # restaurant name
                reviews = data[i]["reviews"] # all reviews

                entry = (name, location["address1"], len(reviews))
                if data[i].get("rating") == 1.0:
                    restaurants_ratings["one"].append(entry)
                if data[i].get("rating") == 2.0:
                    restaurants_ratings["two"].append(entry)
                if data[i].get("rating") == 3.0:
                    restaurants_ratings["three"].append(entry)
                if data[i].get("rating") == 4.0:
                    restaurants_ratings["four"].append(entry)
                if data[i].get("rating") == 5.0:
                    restaurants_ratings["five"].append(entry)

                self.add_element(data_reviews_only, name, location["city"], location["address1"], location["zip_code"], reviews)
        # print(restaurants_ratings)
        print(len(data_reviews_only))
        return data_reviews_only

    # give restaurants with rating 3.0
    # {name: {city: city, address: address, zipcode: zipcode, reviews: reviews}}
    def add_element(self, dict_input, name, city, address, zipcode, reviews):
        new_dict = {"city": city, "address": address, "zipcode": zipcode, "reviews": reviews}
        # If the key exists, append the review to the existing list of reviews
        if name in dict_input:
            dict_input[name].append(new_dict)
        # If the key doesn't exist, create a new key-value pair
        else:
            dict_input[name] = [new_dict]

    def get_topic(self, user_input):
        try:
            topic = re.search('about the (.+?) at', user_input).group(1)
        except:
            topic = None
        return topic

    def get_restuarant(self, user_input):
        if user_input.partition("at ")[2] == "":
            restaurant = user_input.partition("about ")[2]
        else:
            restaurant = user_input.partition("at ")[2]
        return restaurant

    def get_zip(self, user_input):
        try:
            zip = user_input.partition("in ")[2]
        except:
            zip = None
        return zip

    def get_topic_and_restaurant(self, user_input):
        topic = self.get_topic(user_input)
        restaurant = self.get_restuarant(user_input)
        return topic, restaurant

    def get_topic_and_restaurant_with_location(self, user_input):
        topic = self.get_topic(user_input)
        restaurant = self.get_restuarant(user_input)
        zip = self.get_zip(user_input)
        print("\tTopic: ", topic)
        print("\tRestaurant: ", restaurant)
        print("\tZip Code: ",zip)
        return topic, restaurant, zip

    def fetch_reviews(self, user_input):
        topic, restaurant = self.get_topic_and_restaurant(user_input)
        restaurant_data = self.data_reviews_only[restaurant]
        num_locations = len(restaurant_data)
        location_idx = ""
        location_key = ""
        if num_locations > 1:
            return restaurant_data # return list of location data
        else:
            reviews = restaurant_data[0].get("reviews", [])
        print("\tReview from:", f"{restaurant_data[0].get('address')} in {restaurant_data[0].get('city')}")
        return reviews
        # print("\tReviews: ", reviews)

    def fetch_all_locations_by_city(self, city, restaurant):
        restaurant_data = self.data_reviews_only[restaurant]
        locations = []
        for r in restaurant_data:
            if r.get("city") == city:
                locations.append(r)
        return locations

    def is_valid_city(self, user_input, restaurant):
        restaurant_data = self.data_reviews_only[restaurant]
        for r in restaurant_data:
            if r.get("city") == user_input:
                return True
            else:
                continue
        return False

if __name__ == "__main__":
    print("Hello, World!")
    file_path = r'dump_data/yelp_data.bson'
    yelp_handler = Yelp_Data(file_path)
    # user_input = input("User Input: ")#"Tell me about the ambiance at MOD Pizza"
    # reviews = yelp_reviews.fetch_reviews(user_input)
    # for i in reviews:
    #     print(i)
    initial_utterance = True
    restaurant = ''
    city_confirmed = False
    while True:
        user_input = input("User Input: ")
        if user_input == "q":
            break
        if initial_utterance:
            topics_user_spec, restaurant = yelp_handler.get_topic_and_restaurant(user_input)
            print(topics_user_spec)
            print(restaurant)
            topics = [topics_user_spec]
            reviews = yelp_handler.fetch_reviews(user_input)
            if len(reviews) > 0 and isinstance(reviews[0], dict):
                # case where there are multiple locations
                initial_utterance = False
                print(f"There are multiple locations for {restaurant}. Which city would you like to search in?")
            else:
                print(reviews)
        else:
            if yelp_handler.is_valid_city(user_input, restaurant) and not user_input.isnumeric():
                options = yelp_handler.fetch_all_locations_by_city(user_input, restaurant)
                if len(options) > 1:
                    # case where there are multiple locations in the city
                    # {location: reviews}
                    i = 1
                    locations = ""
                    for location in options:
                        locations += f"{i}. {location.get('address')}\n"
                        i += 1
                    city_confirmed = True
                    print(f"There are multiple locations in {user_input}, select the location number from the following options: \n{locations}")
                # return self._main_flow(self.options[0].get("reviews"), dialog_history, system_parameters)
            elif user_input.isnumeric() and city_confirmed:
                index = int(user_input)
                location = options[index - 1]
                reviews = location.get("reviews")
                print(reviews)
                # return self._main_flow(reviews, dialog_history, system_parameters)
            else:
                print("Cannot process request: Enter City Again?")