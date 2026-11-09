system_prompt_ori = """
You are an expert data quality evaluator specializing in financial datasets for Large Language Models. Your task is to evaluate a financial data sample consisting of a financial report (Pre-Text, Table, Post-Text), a Question(or the last question of a series of questions), and a Code Answer. 

You must evaluate the data sample based on the following five criteria. Score each criterion on a continuous scale from 0.0 to 10.0 (float).

[Criteria]
1. **Correctness of the Code Answer**: The provided code must execute without errors and produce the factually correct numerical answer to the **Question** based *only* on the given context (**Pre-Text**, **Post-Text**) and **Table**. This is the most critical criterion.
2. **Relevance and Sufficiency of Information**: The **Question** must be answerable using *only* the information provided in the context and **Table**. No external knowledge should be required. Conversely, the context and **Table** should contain all necessary information to answer the question.
3. **Clarity and Unambiguity of the Question**: The **Question** must be clearly phrased, specific, and have only one correct interpretation. It should be a realistic financial analysis question.
4. **Quality of the Code Answer**: Beyond being correct, the code should be simple, efficient, and easy to understand. It should use standard libraries appropriately and avoid unnecessary complexity or redundant steps. The logic should be straightforward and directly reflect the reasoning process required to answer the question. (Note: The code may be simple and not rely on external libraries; evaluate based on clarity and efficiency given its simplicity.)
5. **Quality and Realism of Context/Table**: The **Pre-Text**, **Post-Text**, and **Table** should be realistic, internally consistent, and free from obvious errors or typos. The data should represent a plausible financial scenario.

[Output Format]
The answer consists of two parts: the thinking process and the answer.

**Thinking Process**: The thinking process is enclosed in <think> and </think> tags, and its content is the step-by-step thinking process for scoring.

**Answer**: You must output your evaluation strictly as a JSON object. 

Use the following strict JSON structure:
{
  "correctness_of_code_answer": <float>,
  "relevance_and_sufficiency": <float>,
  "clarity_of_question": <float>,
  "quality_of_code_answer": <float>,
  "quality_of_context": <float>
}

"""


def create_reader_request_processed(data_sample):
    """Creates the user prompt containing the specific data sample for evaluation."""

    user_prompt_template = """
Please evaluate the following data sample based on the instructions in the system prompt.
[Data Begin]
***
[Pre-Text]: 
{pre_text}
***
[Table]: 
{table}
***
[Post-Text]: 
{post_text}
***
[Questions]: 
{questions}
***
[Question]: {question}
***
[Code Answer]:
```python
{code}
```
[Data End]
"""

    if "questions" in data_sample:
        questions = data_sample.get('questions', "")
    else:
        questions = ""
    question = data_sample.get('question', "")

    user_prompt = user_prompt_template.format(
        pre_text=data_sample.get('pre_text', 'N/A'),
        table=data_sample.get('table', 'N/A'),
        post_text=data_sample.get('post_text', 'N/A'),
        questions=questions,
        question=question,
        code=data_sample.get('code', '# No code provided'),
    )
    return str(user_prompt)


def create_reader_response(data_sample):
    think = '<think>' + data_sample['response']['think'] + '</think>'
    answer = '<answer>' + data_sample['response']['answer'] + '</answer>'
    return think + answer
