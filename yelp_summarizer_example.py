from pipelines.review_chatbot import Chatbot
from argparse import Namespace


if __name__ == "__main__":
    args = Namespace(pipeline='reviews', engine='gpt-4', max_tokens=250, temperature=1.0, top_p=0.9,
                     frequency_penalty=0.0, presence_penalty=0.0, evi_num=2, output_file='data/demo.txt',
                     no_logging=False, debug_mode=False, quit_commands=['quit', 'q', 'Exit'])
    yelp_summarizer = Chatbot(args, 'pipelines/final_project')
    print(yelp_summarizer.generate_response("Kantine", "food quality"))
    print("--------------")
    print(yelp_summarizer.generate_response("MOD Pizza", "food quality", "5263 Prospect Rd"))