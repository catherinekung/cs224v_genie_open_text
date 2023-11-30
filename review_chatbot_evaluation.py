from pipelines.review_chatbot import Chatbot
from argparse import Namespace

restaurants_by_rating = {1: [("Butter Chicken Snob", '150 S 1st St'), ("Beverly Hills Burger Bungalow", '890 Aldo Ave'),
                             "Tamale Barn", "Betty Jeanz Sole Food"],
               2: ["La Kbaña Del Tio Tavito", ("Weinerschnitzel", "411 N Capitol Ave"),
                   ("Wingstop", "171 Branham Ln"), "Z Bar & Restaurant"],
               3: ["Fu Kee Restaurant", "La Tradición De Nueva Italia", "Las Micheladas", "Quarantine Express"],
               4: ["The Creek Eatery", "Stratus Restaurant and Bar", "hashtable", "DV Cafe"],
               5: ["California MoMo Kitchen", "Maxine Kitchen", "Taquisas Los Juanes", "Bay Taco Fish"]}

args = Namespace(pipeline='reviews', engine='gpt-35-turbo', max_tokens=250, temperature=1.0, top_p=0.9, frequency_penalty=0.0, presence_penalty=0.0, evi_num=2, output_file='data/demo.txt', no_logging=False, debug_mode=False, quit_commands=['quit', 'q', 'Exit'])
chatbot = Chatbot(args)


def evaluate():
    for rating in restaurants_by_rating:
        restaurants = restaurants_by_rating[rating]
        for r in restaurants:
            name = r if isinstance(r, str) else r[0]
            print(f"Getting summary for {name}")
            chatbot.restaurant = name
            chatbot.topics = ["ambiance"]
            reviews = chatbot.yelp_handler.fetch_reviews(f"Tell me about the ambiance at {name}")
            if len(reviews) > 0 and isinstance(reviews[0], dict):
                for location in reviews:
                    if location.get("address") == r[1]:
                        chatbot._main_flow(location.get("reviews"), [])
            else:
                chatbot._main_flow(reviews, [])


if __name__ == "__main__":
    evaluate()
