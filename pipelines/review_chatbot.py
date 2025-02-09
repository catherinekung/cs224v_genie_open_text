import time
from typing import List
import logging
import pandas as pd
from .dialog_turn import DialogueTurn
from .final_project.reviews_util import (extract_relevant_content, transform_to_bullet_points,
                                         summarize_reviews, extract_topics_from_review, get_topics_from_response,
                                         generalize_topics)
from .final_project.read_mongo_data import Yelp_Data
import json
import os
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)


class Chatbot:
    """
    Chatbot for CS224V Final Project
    """

    def __init__(self, args, project_file_path) -> None:
        self.project_file_path = project_file_path
        self.args = args
        self.restaurant = ""
        self.city_confirmed = False
        self.topics = []
        self.locations = []
        self.extracted_content = []
        self.yelp_handler = Yelp_Data(project_file_path + '/dump_data/yelp_data.bson')
        self.initial_utterance = True # Tell me about {topic} at {restaurant}
        self.options = None
        self.restaurant_topic_mapping = {}
        self.restaurant_summary_mapping = {}
        self.pick_topic = False
        self.ending_statement = False
        self.choose_location = False
        self._preprocess_steps()

    def _preprocess_steps(self):
        # generate top five topics per restaurant and generate the summaries for those restaurants to be stored
        topic_file_path = self.project_file_path + "/dump_data/restaurant_topics_kantine.json"
        if os.path.exists(topic_file_path):
            with open(topic_file_path, "r") as file:
                self.restaurant_topic_mapping = json.load(file)
        else:
            self._generate_top_topics_per_restaurant()

        summary_file_path = self.project_file_path + "/dump_data/restaurant_summaries_kantine.json"
        if os.path.exists(summary_file_path):
            with open(summary_file_path, "r") as file:
                self.restaurant_summary_mapping = json.load(file)
        else:
            self._generate_summaries_based_on_top_topics()

    def _generate_top_topics_per_restaurant(self):
        restaurant_topic_store = {}
        for restaurant, value in self.yelp_handler.data_reviews_only.items():
            if restaurant == "Kantine":
                for location in value:
                    print(f"Getting topics for {restaurant} on {location.get('address')}")
                    topics_all = []
                    for review in location.get("reviews"):
                        response_review = extract_topics_from_review(review, self.args)
                        topic_list = get_topics_from_response(response_review)
                        topics_all += topic_list
                    print("Finished getting all topics for all reviews. Generalizing topics...")
                    response_generalized = generalize_topics(topics_all, self.args)
                    top_topics = get_topics_from_response(response_generalized)
                    print(f"Top 5 topics: {top_topics}")
                    # location["topics"] = top_topics # modifies in place

                    # dump to local file
                    if len(value) == 1:
                        restaurant_topic_store[restaurant] = top_topics
                    else:
                        entry = {"city": location.get("city"), "address": location.get("address"),
                                 "topics": top_topics}
                        if restaurant not in restaurant_topic_store:
                            restaurant_topic_store[restaurant] = [entry]
                        else:
                            restaurant_topic_store[restaurant].append(entry)

        self.restaurant_topic_mapping = restaurant_topic_store
        with open(self.project_file_path + '/dump_data/restaurant_topics_kantine.json', 'w') as file:
            json.dump(restaurant_topic_store, file)

    def _generate_summaries_based_on_top_topics(self):
        restaurant_summary_store = defaultdict(list)
        # {restaurant: [{topic1: summary, topic2:summary}]
        for restaurant in self.restaurant_topic_mapping:
            self.restaurant = restaurant
            value = self.restaurant_topic_mapping[restaurant]
            reviews = self.yelp_handler.fetch_reviews(f"Tell me about {restaurant}")
            if isinstance(value[0], str):
                topic_summary_mapping = {}
                for topic in value:
                    self.topics = [topic]
                    summary = self._main_flow(reviews, [], False)
                    topic_summary_mapping[topic] = summary
                restaurant_summary_store[restaurant].append(topic_summary_mapping)
            else:
                for i in range(len(value)):
                    loc_review = reviews[i].get("reviews")
                    topics = value[i].get("topics")
                    assert reviews[i].get("address") == value[i].get("address")
                    topic_summary_mapping = {}
                    for topic in topics:
                        self.topics = [topic]
                        summary = self._main_flow(loc_review, [], False)
                        topic_summary_mapping[topic] = summary
                    restaurant_summary_store[restaurant].append({"topics": topic_summary_mapping, "city": reviews[i].get("city"), "address": reviews[i].get("address")})

        with open(self.project_file_path + '/dump_data/restaurant_summaries_kantine.json', 'w') as file:
            json.dump(restaurant_summary_store, file)

    def generate_next_turn(
            self,
            object_dlg_history: List[DialogueTurn],
            new_user_utterance: str,
            pipeline: str,
            system_parameters: dict = {},
            original_reply: str = "",
    ):
        """
        Generate the next turn of the dialog
        system_parameters: can override self.args. Only supports "engine" for now
        """
        # throw error if system_parameters contains keys that are not supported
        for key in system_parameters:
            assert key in ["engine"], f"Unsupported system_parameter key: {key}"

        start_time = time.time()

        if pipeline == "reviews":
            reply = self._generate_review_topics(
                object_dlg_history,
                new_user_utterance=new_user_utterance
            )
            new_dlg_turn = DialogueTurn(user_utterance=new_user_utterance)
            new_dlg_turn.gpt3_agent_utterance = reply
            new_dlg_turn.agent_utterance = reply
        else:
            raise ValueError

        new_dlg_turn.engine = system_parameters.get("engine", self.args.engine)
        new_dlg_turn.pipeline = pipeline

        end_time = time.time()
        new_dlg_turn.wall_time_seconds = end_time - start_time
        new_dlg_turn.dlg_history = object_dlg_history

        return new_dlg_turn

    def _output_to_csv(self, reviews, relevent_content, replies, summary, filename):
        # print(self.review_list)
        # print(self.reply_list)
        # dictionary of lists
        reviews.append(" ")
        replies.append(" ")
        self.extracted_content.append(" ")

        summaries = [" "] * (len(reviews) - 1)
        summaries.append(summary)
        comments = [" "] * (len(reviews))
        dict = {'Reviews': reviews, 'Relevant Content': self.extracted_content, 'Replies': replies, 'Comments': comments, 'Summary': summaries}
        df = pd.DataFrame(dict)
        df.to_csv(self.project_file_path + "/outputs/" + filename)

    def _main_flow(self, reviews, dialog_history, save_response=True):
        bullet_content = []
        summarization_content = []
        start_time = time.time()
        self.extracted_content = []
        if isinstance(reviews[0], dict):
            reviews = reviews[0].get("reviews")

        for review in reviews:
            relevent_content = extract_relevant_content(review, self.topics, dialog_history, self.args, few_shot=True)
            self.extracted_content.append(relevent_content)
            if "No relevant information found" not in relevent_content and relevent_content != "":
                content = transform_to_bullet_points(relevent_content, dialog_history, self.args)
                bullet_content.append(content)
                summarization_content.append(content)
            else:
                bullet_content.append(" ")

        if all(bullet == " " for bullet in bullet_content):
            topics = " ".join(self.topics)
            reply = f"There is no relevant information regarding the {topics} at {self.restaurant}."
        else:
            reply = summarize_reviews(summarization_content, self.topics, self.restaurant, dialog_history, self.args)
        if save_response:
            epoch = round(time.time())
            csv_file_name = self.restaurant.replace(" ", "_") + "_topic_" + self.topics[0].replace(" ", "_") + "_" + str(epoch) + ".csv"
            self._output_to_csv(reviews, self.extracted_content, bullet_content, reply, csv_file_name)

        end_time = time.time()
        # print("Elapsed Time:" + str((end_time - start_time) / 60) + " minutes")
        self.initial_utterance = False
        return reply

    def initial_interaction(self, new_user_utterance, dialog_history):
        topics_user_spec, self.restaurant = self.yelp_handler.get_topic_and_restaurant(new_user_utterance)
        if self.restaurant not in self.yelp_handler.data_reviews_only:
            return "I do not have information on that restaurant. Let's try again with another restaurant!"
        if not topics_user_spec:
            reviews = self.yelp_handler.fetch_reviews(new_user_utterance)
            if len(reviews) > 0 and isinstance(reviews[0], dict):
                city = "with multiple locations"
                if len(reviews[0]["categories"]) > 0:
                    background = f", a {reviews[0]['categories'][0]['title']} place,"
                else:
                    background = ''
            else:
                city = "in " + self.yelp_handler.data_reviews_only[self.restaurant][0]["city"]
                if len(self.yelp_handler.data_reviews_only[self.restaurant][0]["categories"]) > 0:
                    background = f", a {self.yelp_handler.data_reviews_only[self.restaurant][0]['categories'][0]['title']} place,"
                else:
                    background = ''
            if self.restaurant in self.restaurant_topic_mapping:
                self.topics = self.restaurant_topic_mapping[self.restaurant]  # return list of top 5 topics
                self.pick_topic = True
                return f"I found a restaurant called {self.restaurant}{background} {city}. I see that you did not provide a specific topic of interest regarding {self.restaurant}! Most reviews talked either about {', '.join(self.topics[:4])}, or {self.topics[4]}. Would you like to learn more about one of these topics?"
            self.pick_topic = True
            return f"I found a restaurant called {self.restaurant}{background} {city}. I see that you did not provide a specific topic of interest regarding {self.restaurant}! Some common topics regarding restaurants include ambiance, service, food quality and pricing. Would you like to learn more about one of these topics?"
        else:
            self.topics = [topics_user_spec]
        # print(self.topics)
        # print(self.restaurant)
        if self.restaurant in self.restaurant_summary_mapping and topics_user_spec in \
                self.restaurant_summary_mapping[self.restaurant][0]:
            self.initial_utterance = False
            return self.restaurant_summary_mapping[self.restaurant][0][topics_user_spec] + " Is there anything else I can help you with?"
        reviews = self.yelp_handler.fetch_reviews(new_user_utterance)
        if len(reviews) > 0 and isinstance(reviews[0], dict):
            # case where there are multiple locations
            self.initial_utterance = False
            cities = [location.get("city") for location in reviews]
            unique_cities = list(set(cities))
            self.choose_location = True
            return f"There are multiple locations for {self.restaurant}. Which city would you like to search in? I found locations in: {', '.join(unique_cities)}."
        else:
            return self._main_flow(reviews, dialog_history) + " Is there anything else I can help you with?"

    def _generate_review_topics(
            self,
            dialog_history: List[DialogueTurn],
            new_user_utterance: str
    ) -> str:
        """
        Generate baseline GPT3 response
        Args:
            - `dialog_history` (list): previous turns
        Returns:
            - `reply`(str): GPT3 original response
        """
        if new_user_utterance == 'Hi!':
            return "Hi, I'm Yelp Summarizer. Ask me anything about a restaurant and I'll try my best to answer it based off of reviews on Yelp!"
        if self.initial_utterance and not self.pick_topic:
            return self.initial_interaction(new_user_utterance, dialog_history)
        elif self.initial_utterance and self.pick_topic:
            topic = new_user_utterance.split(" ")[-1]
            self.topics = [topic]
            # print(self.topics)
            # print(self.restaurant)
            self.pick_topic = False
            self.initial_utterance = False
            reviews = self.yelp_handler.fetch_reviews(f"Tell me about the {topic} at {self.restaurant}")
            if self.restaurant in self.restaurant_summary_mapping and topic in self.restaurant_summary_mapping[self.restaurant][0]:
                return self.restaurant_summary_mapping[self.restaurant][0][topic] + " Is there anything else I can help you with?"
            return self._main_flow(reviews, dialog_history)
        elif not self.initial_utterance and "Tell me about" not in new_user_utterance and not self.choose_location or self.ending_statement:
            return "Thanks for chatting with me. Have a great day!"
        elif not self.initial_utterance and ("Tell me about" in new_user_utterance or "tell me about" in new_user_utterance):
            self.initial_utterance = True
            self.pick_topic = False
            self.city_confirmed = False
            self.choose_location = False
            return self.initial_interaction(new_user_utterance, dialog_history)
        else:
            if self.yelp_handler.is_valid_city(new_user_utterance, self.restaurant) and not new_user_utterance.isnumeric():
                self.options = self.yelp_handler.fetch_all_locations_by_city(new_user_utterance, self.restaurant)
                if len(self.options) > 1:
                    # case where there are multiple locations in the city
                    # [{city: city, address: address, reviews: reviews}]
                    i = 1
                    locations = ""
                    for location in self.options:
                        locations += f"{i}. {location.get('address')}\n"
                        i += 1
                    self.city_confirmed = True
                    return f"There are multiple locations in {new_user_utterance}, select the location number from the following options: \n{locations}"
                self.initial_utterance = False
                return self._main_flow(self.options[0].get("reviews"), dialog_history)
            elif new_user_utterance.isnumeric() and self.city_confirmed:
                index = int(new_user_utterance)
                location = self.options[index-1]
                reviews = location.get("reviews")
                self.initial_utterance = False
                self.choose_location = False
                return self._main_flow(reviews, dialog_history) + " Is there anything else I can help you with?"
            else:
                return f"There isn't a {self.restaurant} in {new_user_utterance}. Enter City Again?"

    def generate_response(self, restaurant, topic, address=None):
        # pass in address if restaurant has multiple locations
        print(f"Generating summary for {restaurant} about {topic}")
        self.restaurant = restaurant
        self.topics = [topic]
        if self.restaurant not in self.yelp_handler.data_reviews_only:
            return "Restaurant not found"
        reviews = self.yelp_handler.fetch_reviews(f"Tell me about the {topic} at {restaurant}")
        if len(reviews) > 0 and isinstance(reviews[0], dict):
            # case where there's multiple locations
            for location in reviews:
                if location.get("address") == address:
                    return self._main_flow(location.get("reviews"), [], True)
            return f"Restaurant with specified location at {address} not found"
        return self._main_flow(reviews, [], True)
