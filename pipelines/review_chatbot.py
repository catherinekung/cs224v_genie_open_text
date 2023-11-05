import time
from typing import List
import logging

from .dialog_turn import DialogueTurn
from .final_project.reviews_util import (extract_relevant_content, is_valid_city,
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

    def _main_flow(self, reviews, dialog_history, system_parameters):
        all_content = []
        start_time = time.time()
        for review in reviews[:1]:
            content = extract_relevant_content(review, self.topics, dialog_history, self.args, system_parameters)
            all_content.append(content)

        end_time = time.time()
        print("Elapsed Time:" + str((end_time - start_time) / 60) + " minutes")
        self.initial_utterance = False
        return "\n".join(all_content)
        # reply = summarize_reviews(all_content)
        # return reply

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
            topics_user_spec, self.restaurant = self.yelp_handler.get_topic_and_restaurant(new_user_utterance)
            self.topics = [topics_user_spec]
            reviews = self.yelp_handler.fetch_reviews(new_user_utterance)
            if len(reviews) > 0 and isinstance(reviews[0], dict):
                # case where there are multiple locations
                self.initial_utterance = False
                return f"There are multiple locations for {self.restaurant}. Which city would you like to search in?"
            else:
                return self._main_flow(reviews, dialog_history, system_parameters)
        else:
            if is_valid_city(new_user_utterance, self.restaurant, self.yelp_handler.data_reviews_only) and not new_user_utterance.isnumeric():
                self.options = self.yelp_handler.fetch_all_locations_by_city(new_user_utterance, self.restaurant)
                if len(self.options) > 1:
                    # case where there are multiple locations in the city
                    # {location: reviews}
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
                return "Cannot process request: Enter City Again?"
