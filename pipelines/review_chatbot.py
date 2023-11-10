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

logger = logging.getLogger(__name__)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)


class Chatbot:
    """
    Chatbot for CS224V Final Project
    """

    def __init__(self, args) -> None:
        self.args = args
        self.restaurant = ""
        self.city_confirmed = False
        self.topics = []
        self.locations = []
        self.yelp_handler = Yelp_Data(r'pipelines/final_project/dump_data/yelp_data.bson')
        self.initial_utterance = True # Tell me about {topic} at {restaurant}
        self.options = None
        self.restaurant_topic_mapping = {}
        self.restaurant_summary_mapping = {}
        self._preprocess_steps()

    def _preprocess_steps(self):
        topic_file_path = "pipelines/final_project/dump_data/restaurant_topics.json"
        if os.path.exists(topic_file_path):
            with open(topic_file_path, "r") as file:
                self.restaurant_topic_mapping = json.load(file)
        else:
            self._generate_top_topics_per_restaurant()

        summary_file_path = "pipelines/final_project/dump_data/restaurant_summaries.json"
        if os.path.exists(summary_file_path):
            with open(summary_file_path, "r") as file:
                self.restaurant_summary_mapping = json.load(file)
        else:
            self._generate_summaries_based_on_top_topics()

    def _generate_top_topics_per_restaurant(self):
        restaurant_topic_store = {}
        for restaurant, value in self.yelp_handler.data_reviews_only.items():
            if restaurant == "HK Dim Sum" or restaurant == "MOD Pizza":
                for location in value:
                    if location.get("address") != "127 Serramonte Ctr":
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
                print(restaurant_topic_store)
        with open('pipelines/final_project/dump_data/restaurant_topics.json', 'w') as file:
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
                    summary = self._main_flow(reviews, [])
                    topic_summary_mapping[topic] = summary
                restaurant_summary_store[restaurant].append(topic_summary_mapping)
            else:
                review_list = self.yelp_handler.fetch_reviews(f"Tell me about {restaurant}")
                for i in range(len(value)):
                    reviews = review_list[i].get("reviews")
                    topics = value[i].get("topics")
                    assert review_list[i].get("address") == value[i].get("address")
                    topic_summary_mapping = {}
                    for topic in topics:
                        self.topics = [topic]
                        summary = self._main_flow(reviews, [])
                        topic_summary_mapping[topic] = summary
                    restaurant_summary_store[restaurant].append(topic_summary_mapping)

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

    def _output_to_csv(self, reviews, replies, summary, filename):
        # print(self.review_list)
        # print(self.reply_list)
        # dictionary of lists
        reviews.append(" ")
        replies.append(" ")
        summaries = [" "] * (len(reviews) - 1)
        summaries.append(summary)
        dict = {'Reviews': reviews, 'Replies': replies, 'Summary': summaries}
        df = pd.DataFrame(dict)
        # saving the dataframe
        df.to_csv("pipelines/final_project/outputs/" + filename)

    def _main_flow(self, reviews, dialog_history):
        bullet_content = []
        summarization_content = []
        start_time = time.time()
        for review in reviews:
            content = extract_relevant_content(review, self.topics, dialog_history, self.args)
            if "No relevant information found" not in content:
                content = transform_to_bullet_points(content, dialog_history, self.args)
                bullet_content.append(content)
                summarization_content.append(content)
            else:
                bullet_content.append(" ")

        reply = summarize_reviews(summarization_content, self.topics, self.restaurant, dialog_history, self.args)
        epoch = round(time.time())
        csv_file_name = self.restaurant.replace(" ", "_") + "_topic_" + self.topics[0].replace(" ", "_") + "_" + str(epoch) + ".csv"
        self._output_to_csv(reviews, bullet_content, reply, csv_file_name)

        end_time = time.time()
        print("Elapsed Time:" + str((end_time - start_time) / 60) + " minutes")
        self.initial_utterance = False
        return reply

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
        if self.initial_utterance:
            new_user_utterance = "Tell me about HK Dim Sum"
            topics_user_spec, self.restaurant = self.yelp_handler.get_topic_and_restaurant(new_user_utterance)
            if not topics_user_spec:
                self.topics = ["ambience"] # return list of top 5 topics
            else:
                self.topics = [topics_user_spec]
            # print(self.topics)
            # print(self.restaurant)
            reviews = self.yelp_handler.fetch_reviews(new_user_utterance)
            if len(reviews) > 0 and isinstance(reviews[0], dict):
                # case where there are multiple locations
                self.initial_utterance = False
                return f"There are multiple locations for {self.restaurant}. Which city would you like to search in?"
            else:
                return self._main_flow(reviews, dialog_history)
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
                return self._main_flow(self.options[0].get("reviews"), dialog_history)
            elif new_user_utterance.isnumeric() and self.city_confirmed:
                index = int(new_user_utterance)
                location = self.options[index-1]
                reviews = location.get("reviews")
                return self._main_flow(reviews, dialog_history)
            else:
                return f"There are isn't a {self.restaurant} in {new_user_utterance}. Enter City Again?"
