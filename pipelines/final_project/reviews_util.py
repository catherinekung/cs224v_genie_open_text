from ..llm import llm_generate


def extract_relevant_content(review, topics, dialog_history, args, system_parameters):
    reply = llm_generate(
        template_file="final_project/prompts/extract_relevant_content_per_topic.prompt",
        prompt_parameter_values={
            "dlg": dialog_history,
            "new_user_utterance": review,
            "topics": topics
        },
        engine=system_parameters.get("engine", args.engine),
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


def extract_topics_from_review(review, dialog_history, args, system_parameters):
    reply = llm_generate(
        template_file="final_project/prompts/identify_topics_from_review.prompt",
        prompt_parameter_values={
            "dlg": dialog_history,
            "new_user_utterance": review
        },
        engine=system_parameters.get("engine", args.engine),
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

def extract_restaurant_topic(user_utterance):
    pass


def fetch_reviews(restaurant):
    pass


def summarize_reviews(reviews):
    pass
