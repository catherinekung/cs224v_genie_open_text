import time
from typing import List
import logging
import pandas as pd
import csv
from .dialog_turn import DialogueTurn
from .final_project.reviews_util import (extract_relevant_content, transform_to_bullet_points,
                                         summarize_reviews, extract_topics_from_review)
from .final_project.read_mongo_data import Yelp_Data

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
        # self.review_list = []
        # self.reply_llist = []
        self.yelp_handler = Yelp_Data(r'pipelines/final_project/dump_data/yelp_data.bson')
        self.initial_utterance = True # Tell me about {topic} at {restaurant}
        self.options = None

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
                new_user_utterance=new_user_utterance,
                system_parameters=system_parameters,
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

    def output_to_csv(self, reviews, replies, summary, filename):
        # dictionary of lists
        dict = {'Reviews': reviews, 'Replies': replies, 'Summary': summary}
        df = pd.DataFrame(dict)
        # saving the dataframe
        df.to_csv("pipelines/final_project/outputs/" + filename)

    def _main_flow(self, reviews, dialog_history, system_parameters):
        bullet_content = []
        summarization_content = []
        start_time = time.time()
        for review in reviews:
            content = extract_relevant_content(review, self.topics, dialog_history, self.args, system_parameters)
            if "No relevant information found" not in content:
                content = transform_to_bullet_points(content, dialog_history, self.args, system_parameters)
                bullet_content.append(content)
                summarization_content.append(content)
            else:
                bullet_content.append(" ")

        reply = summarize_reviews(summarization_content, self.topics, self.restaurant, dialog_history, self.args, system_parameters)
        epoch = round(time.time())
        csv_file_name = self.restaurant.replace(" ", "_") + "_topic_" + self.topics[0].replace(" ", "_") + "_" + str(epoch) + ".csv"
        self.output_to_csv(reviews, bullet_content, reply, csv_file_name)

        end_time = time.time()
        print("Elapsed Time:" + str((end_time - start_time) / 60) + " minutes")
        self.initial_utterance = False
        return reply

    def _generate_review_topics(
            self,
            dialog_history: List[DialogueTurn],
            new_user_utterance: str,
            system_parameters: dict,
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
            if topics_user_spec == None:
                self.topics = ["ambience"]
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
                return self._main_flow(reviews, dialog_history, system_parameters)
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
                return self._main_flow(self.options[0].get("reviews"), dialog_history, system_parameters)
            elif new_user_utterance.isnumeric() and self.city_confirmed:
                index = int(new_user_utterance)
                location = self.options[index-1]
                reviews = location.get("reviews")
                return self._main_flow(reviews, dialog_history, system_parameters)
            else:
                return f"There are isn't a {self.restaurant} in {new_user_utterance}. Enter City Again?"
