from ..llm import llm_generate
# review_list = []
# reply_list = []
def extract_relevant_content(review, topics, dialog_history, args, system_parameters):
    # seems to seek other topics if only one is given, so splitting up into two cases
    if len(topics) > 1:
        template_file = "final_project/prompts/extract_relevant_content_per_topic.prompt"
    else:
        template_file = "final_project/prompts/extract_relevant_content_single_topic.prompt"
    reply = llm_generate(
        template_file=template_file,
        prompt_parameter_values={
            "dlg": dialog_history,
            "new_user_utterance": review,
            "topics": topics
        },
        engine=system_parameters.get("engine", args.engine),
        max_tokens=args.max_tokens, # check if 200 is enough
        temperature=args.temperature,
        stop_tokens=[],
        top_p=args.top_p,
        frequency_penalty=args.frequency_penalty,
        presence_penalty=args.presence_penalty,
        postprocess=True,
        ban_line_break_start=True,
    )
    # if len(dialog_history) > 0:
    #     for i in range(len(dialog_history)):
    #         print("User: ", dialog_history[i].user_utterance)
    #         print("Chatbot:", dialog_history[i].agent_utterance)
    #         print("Reviews", review)
    #         print("Chatbot Response", reply)
    # else:
    #     print("Reviews", review)
    #     print("Chatbot Response", reply)
    # review_list.append(review)
    # reply_list.append(reply)
    return reply #, review_list, reply_list


def transform_to_bullet_points(relevant_sentences, dialog_history, args, system_parameters):
    reply = llm_generate(
        template_file="final_project/prompts/transform_to_bullet_points.prompt",
        prompt_parameter_values={
            "dlg": dialog_history,
            "new_user_utterance": relevant_sentences,
        },
        engine=system_parameters.get("engine", args.engine),
        max_tokens=args.max_tokens, # check if 200 is enough
        temperature=args.temperature,
        stop_tokens=[],
        top_p=args.top_p,
        frequency_penalty=args.frequency_penalty,
        presence_penalty=args.presence_penalty,
        postprocess=True,
        ban_line_break_start=True,
    )

    return reply


def extract_topics_from_review(review, dialog_history, args, system_parameters):
    reply = llm_generate(
        template_file="final_project/prompts/identify_topics_from_review.prompt",
        prompt_parameter_values={
            "dlg": dialog_history,
            "new_user_utterance": review
        },
        engine=system_parameters.get("engine", args.engine),
        max_tokens=args.max_tokens, # default 200, double check
        temperature=args.temperature, # lower temp for higher accuracy
        stop_tokens=[],
        top_p=args.top_p,
        frequency_penalty=args.frequency_penalty,
        presence_penalty=args.presence_penalty,
        postprocess=True,
        ban_line_break_start=True, # can set to true/false
    )

    return reply


# def is_valid_city(user_input, restaurant, dict):
#     restaurant_data = dict[restaurant]
#     for r in restaurant_data:
#         if r.get("city") == user_input:
#             return True
#         else:
#             continue
#     return False
    # call llm


def summarize_reviews(reviews):
    pass
