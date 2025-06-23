def analyze(topic: str, context: list, agent, context_window: int):
    prompt = f"Use these web search results to answer this question: {topic}. Here are the results: {context}"
    response = agent.model.get_response(prompt, context_window=context_window)
    return response


def critisize(analysis: str, context: list, agent, context_window: int) -> str:
    prompt = f"""Critically evaluate the following analysis. Identify any potential biases,
                    unstated assumptions, or logical fallacies. Is the evidence strong enough
                    to support the conclusions? Return your findings in a paragraph. 

                    --- ANALYSIS ---
                    {analysis}

                    --- SOURCES --- 
                    {context}
                    """
    response = agent.model.get_response(prompt, context_window=context_window)
    return response


def synthesize(analysis: str, criticism: str, agent, context_window: int):
    prompt = f"""Create a coherent summary that incorporates the initial analysis and the subsequent critique.
                Present a balanced view based on both pieces of information.

                --- INITIAL ANALYSIS ---
                {analysis}

                --- CRITIQUE ---
                {criticism}
                """
    response = agent.model.get_response(prompt, context_window=context_window)
    return response


def next_step(synthesis: str, origin_topic: str, agent, context_window: int) -> str:
    prompt = f"""
            Based on the following research summary and critique, what are the most
            important unanswered questions or next steps for a deeper investigation? Determine the most important details and create a question. Respond with only the question you create. 

            --- SUMMARY ---
            {synthesis}
            
            STAY ON TOPIC WITH THE ORIGIN TOPIC: {origin_topic}                
            """

    response = agent.model.get_response(prompt, context_window=context_window)
    return response
