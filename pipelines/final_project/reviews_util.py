from ..llm import llm_generate
import re

def extract_relevant_content(review, topics, dialog_history, args, few_shot):
    # seems to seek other topics if only one is given, so splitting up into two cases
    if len(topics) > 1:
        template_file = "final_project/prompts/extract_relevant_content_per_topic.prompt"
    else:
        if few_shot:
            template_file = "final_project/prompts/extract_relevant_bullets_single_topic_few_shot.prompt"
        else:
            template_file = "final_project/prompts/extract_relevant_bullets_single_topic_zero_shot.prompt"
    print(template_file)
    prompt_parameters = {
        "dlg": dialog_history,
        "new_user_utterance": review,
        "topics": topics
    }
    reply = generate_response(template_file, prompt_parameters, args)
    return reply


def transform_to_bullet_points(relevant_sentences, dialog_history, args):
    template_file = "final_project/prompts/transform_to_bullet_points_2.prompt"
    prompt_parameters = {
        "dlg": dialog_history,
        "new_user_utterance": relevant_sentences,
    }
    reply = generate_response(template_file, prompt_parameters, args)
    return reply


def extract_topics_from_review(review, args):
    template_file = "final_project/prompts/identify_topics_from_review.prompt"
    prompt_parameters = {
        "new_user_utterance": review
    }
    reply = generate_response(template_file, prompt_parameters, args)
    return reply


def get_topics_from_response(response):
    # topics identified=[location, seating, staff, food, entertainment]
    try:
        topics = re.search("topics identified=(\[[^\[]*\])", response).group(1)
        topic_list = topics.strip('][').split(', ')
        return topic_list
    except:
        print(f"Could not get topics from response={response}")
        return "[]"


def generalize_topics(topic_list, args):
    template_file = "final_project/prompts/generalize_topics_from_review.prompt"
    prompt_parameters = {
        "new_user_utterance": topic_list
    }
    reply = generate_response(template_file, prompt_parameters, args)
    return reply

def summarize_reviews(bullet_points, topics, restaurant, dialog_history, args):
    template_file = "final_project/prompts/summarize_bullet_points_2.prompt"
    prompt_parameters = {
        "dlg": dialog_history,
        "new_user_utterance": bullet_points,
        "topics": ", ".join(topics),
        "restaurant": restaurant
    }
    reply = generate_response(template_file, prompt_parameters, args)
    return reply


def generate_response(template_file, prompt_parameters, args):
    try:
        reply = llm_generate(
            template_file=template_file,
            prompt_parameter_values=prompt_parameters,
            engine=args.engine,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            stop_tokens=[],
            top_p=args.top_p,
            frequency_penalty=args.frequency_penalty,
            presence_penalty=args.presence_penalty,
            postprocess=True,
            ban_line_break_start=True,
        )
        return reply
    except Exception as e:
        print("An error occurred when calling the LLM", e)
        return ""


