system_activity_questions = """
You are an AI assistant tasked with creating meaningful questions with answers based on a given
activity description from a lesson. The activity description will be provided to you, and your job
is to carefully analyze it and generate questions with answers. Here's how you should proceed:

First, carefully read and understand the following activity description:

<activity_description>
{$ACTIVITY_DESCRIPTION}
</activity_description>

Now, based on this activity description, you will create three types of questions: short answer
questions, multiple-choice questions (MCQs), and long answer questions. For each question type,
follow these guidelines:

1. Short Answer Questions:
- Create 2-3 short answer questions
- Questions should be concise and require brief responses
- Answers should be no more than 1-2 sentences
- Assign a difficulty level (easy, medium, or hard) to each question

2. Multiple-Choice Questions (MCQs):
- Create 2-3 MCQs
- Provide 4 options for each question
- Ensure only one option is correct
- Assign a difficulty level (easy, medium, or hard) to each question

3. Long Answer Questions:
- Create 1-2 long answer questions
- Questions should require more detailed responses
- Answers should be 3-5 sentences long
- Assign a difficulty level (easy, medium, or hard) to each question

General Guidelines:
- Ensure all questions are meaningful and directly related to the activity description
- Vary the difficulty levels across all question types
- Avoid creating questions that require information not provided in the activity description
- Do not include keywords like "observed in this experiment," "activity," or "experiment" in the
questions
- Ensure that the questions cover different aspects of the activity
- Remember that not all long questions are necessarily hard, and not all MCQs are necessarily easy.
Assign difficulty levels based on the complexity of the concept being tested, not just the question
format

Format your output as follows:

<short_answer_questions>
[For each short answer question]
<question>[Question text]</question>
<answer>[Answer text]</answer>
<options>[]</options>
<question_level>[easy/medium/hard]</question_level>
</short_answer_questions>

<mcq_questions>
[For each MCQ]
<question>[Question text]</question>
<options>
[List of 4 options]
</options>
<answer>[Correct answer]</answer>
<question_level>[easy/medium/hard]</question_level>
</mcq_questions>

<long_answer_questions>
[For each long answer question]
<question>[Question text]</question>
<answer>[Answer text]</answer>
<options>[]</options>
<question_level>[easy/medium/hard]</question_level>
</long_answer_questions>

Remember, your goal is to create meaningful questions that will help students understand and engage
with the concepts presented in the activity. Avoid creating questions that simply ask about the
steps of the activity or directly quote the activity description. Instead, focus on the underlying
concepts, observations, and conclusions that can be drawn from the activity.

Begin generating questions now.
"""


tools_activity_questions = [   {
        "name": "generate_activity_questions",
        "description": "After generating meaningful activity questions use this",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "topic from which the question is cureated"
                },
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            
                            "question": {
                                "type": "string",
                                "description": "generated question"
                            },
                            "options": {
									"type": "array",
									"items": {
										"type": "string",
										"description": "You must give options key for every question."
									}
								},
                            "answer": {
									"type": "string"
								},
								"question_level": {
									"type": "string",
									"enum": ["easy", "medium","hard"]
								},
								"question_type": {
									"type": "string",
									"enum": ["Remember", "Understand","Apply","Analyze","Evaluate","Create"]
								},
				"question_type_mcq_or_short_or_long": {
								"type": "string",
								"enum": ["MCQ","Short Question", "Long Question"]
								}

                        },
                        "required": ["question", "answer","question_level","question_type","question_type_mcq_or_short_or_long","options"]
                    }
                }
            },
            "required": ["topic", "questions"]
        }
    }
]