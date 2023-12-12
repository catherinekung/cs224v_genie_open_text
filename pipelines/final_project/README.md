# CS224V Final Project

## Setup
Follow the [Setup](https://github.com/catherinekung/cs224v_genie_open_text#setup) in the root directory of this repo.

## Modifications to Original Repo
We leveraged the existing chatbot flow in this repo and made the following changes:
- Replaced [Chatbot](https://github.com/catherinekung/cs224v_genie_open_text/blob/main/chat_interactive.py#L30) with our Yelp Summarizer defined [here](https://github.com/catherinekung/cs224v_genie_open_text/blob/main/pipelines/review_chatbot.py)
- Updated [pipeline arguments](https://github.com/catherinekung/cs224v_genie_open_text/blob/main/pipelines/pipeline_arguments.py#L19) to include our `reviews` pipeline 

## Key Files in the `final_project` Directory
- `read_mongo_data.py`: parses and fetches reviews and metadata from our local dump of Yelp review data
- `reviews_util.py`: utility functions used to call the LLMs 
- `/prompts`: we used the following prompts in our final pipeline
  - `identify_topics_from_review.prompt`: identifies all topics mentioned in a single review for a restaurant
  - `generalize_topics_from_review.prompt`: returns top 5 topics mentioned in reviews for a restaurant
  - `extract_relevant_content_single_topic_few_shot.prompt`: extract portions of a review that are relevant to the given topic 
  - `transform_to_bullet_points_2.prompt`: condenses all relevant content from all reviews into bullet points
  - `summarize_bullet_points_2.prompt`: summarize all bullet points into final response


## Run Yelp Summarizer
Begin by navigating to root directory.

Run the chat interface and prompt with `Tell me about {topic} at {restaurant}`
```
python3 chat_interactive.py
```

Generate a summary for a given restaurant and topic (can modify [examples](https://github.com/catherinekung/cs224v_genie_open_text/blob/main/yelp_summarizer_example.py#L10) before generating) 
```
python3 yelp_summarizer_example.py
```

