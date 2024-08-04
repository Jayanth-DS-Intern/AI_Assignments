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


system_case_based_questions = """

You are tasked with creating a case study and related questions based on a given subtopic from a
school lesson. Your goal is to generate engaging and educational content that tests students'
understanding of the subject matter.

Here is the subtopic you will be working with:
<subtopic>
{$SUBTOPIC}
</subtopic>

First, create a case study based on this subtopic. The case study should be a short paragraph (3-5
sentences) that provides context and information related to the subtopic. Make sure the case study
is factual, informative, and appropriate for students in grades 6-10.

After creating the case study, generate 4 questions based on the information provided in the case
study. Follow these guidelines for the questions:

0.The first question should include the case study. For any subsequent questions (if applicable),
the case study should be an empty list([])
1. All questions must be directly related to the case study.
2. Include a mix of difficulty levels (easy, medium, hard).
3. Use a variety of question types (multiple choice, short answer, true/false).
4. For multiple choice questions, provide 4 options.
5. Include the correct answer for each question.
6. For non-multiple choice questions, provide a brief explanation of the answer.

Remember: Include the case study only for the first question; use an empty list ([]) for any subsequent
questions

Present your output in the following format:

<case_study>
[Insert your case study here]
</case_study>

<questions>
<question1>
case_study:[Insert your case study here]
Question: [Insert question here]
Options: [If multiple choice, list 4 options here] else []
Answer: [Insert correct answer here]
Explanation: [For non-multiple choice questions, provide a brief explanation]
Difficulty: [Easy/Medium/Hard]
</question1>

[Repeat the above structure for questions 2, 3, and 4]
</questions>

Remember to stay within the scope of the given subtopic and case study. Do not introduce new
information that is not mentioned in the case study when creating questions.

Here are two examples for reference:

Example 1:

<questions>
<question1>
case_study: Carbohydrates, proteins, fats, vitamins, and minerals are components of food. These components of
food are called nutrients and are necessary for our bodies. All living organisms require food.
Plants can synthesize food for themselves but animals including humans cannot. They get it from
plants or animals that eat plants. Thus, humans and animals are directly or indirectly dependent on
plants. Plants are the only organisms that can prepare food for themselves using water, carbon
dioxide, and minerals. The raw materials are present in their surroundings. The nutrients enable
living organisms to build their bodies, grow, repair damaged parts of their bodies, and provide the
energy to carry out life processes. Nutrition is the mode of taking food by an organism and its
utilization by the body. The mode of nutrition in which organisms make food themselves from simple
substances is called autotrophic (auto = self; trophos= nourishment) nutrition. Therefore, plants
are called autotrophs. Animals and most other organisms take in food prepared by plants. They are
called heterotrophs (heteros = other).
Question: What are the components of food?
Options: ["Vitamins", "Carbohydrates", "Proteins", "All the above"]
Answer: All the above
Difficulty: Easy
</question1>

<question2>
case_study: []
Question: Which organisms are autotrophs?
options: []
Answer: Autotrophs are organisms that can produce their own food through photosynthesis or
chemosynthesis. They are also known as producers because they create nutrients and energy for other
organisms in the food chain.
Difficulty: Medium
</question2>

<question3>
case_study: []
Question: What are the things enabled by nutrients to living organisms?
options: []
Answer: Nutrients help break down food to give organisms energy. They are used in every process of
an organism's body. Some of the processes are growth (building cells), repair (healing a wound), and
maintaining life (breathing).
Difficulty: Easy
</question3>

<question4>
case_study: []
Question: Why are animals and humans considered heterotrophs?
options = []
Answer: Animals and humans are considered heterotrophs because they cannot produce their own food
and must obtain nutrients by consuming other organisms or their products. They rely directly or
indirectly on plants, which are autotrophs, for their food source.
Difficulty: Medium
</question4>
</questions>

Example 2:

<questions>
<question1>
case_study: Leaves are the food factories of plants. Therefore, all the raw materials must reach the leaf. Water
and minerals present in the soil are absorbed by the roots and transported to the leaves. Carbon
dioxide from the air is taken in through the tiny pores present on the surface of leaves. These
pores are surrounded by 'guard cells'. Such pores are called stomata. Water and minerals are
transported to the leaves by the vessels which run like pipes throughout the root, the stem, the
branches, and the leaves. They form a continuous path or passage for the nutrients to reach the
leaf. They are called vessels.
Question: _____ is the ultimate source of energy for all living organisms.
Options: ["Visible light", "Infrared light", "Sun", "Moon"]
Answer: Sun
Difficulty: Medium
</question1>

<question2>
case_study: []
Question: The process of synthesis of food from carbon dioxide and water in the presence of sunlight
is called ______.
Options: ["Photosynthesis", "Pigmentation", "Reproduction", "None of the above"]
Answer: Photosynthesis
Difficulty: Easy
</question2>

<question3>
case_study: []
Question: What are stomata?
Answer: Stomata are tiny pores present on the surface of leaves, surrounded by guard cells. They
allow for the intake of carbon dioxide from the air, which is necessary for photosynthesis.
Difficulty: Medium
</question3>

<question4>
case_study: []
Question: True or False: Vessels in plants transport only water to the leaves.
Answer: False
Explanation: Vessels in plants transport both water and minerals to the leaves. They form a
continuous path throughout the plant, from the roots to the leaves, allowing for the transportation
of necessary nutrients.
Difficulty: Easy
</question4>
</questions>

Now, proceed to create a case study and questions based on the given subtopic.
"""

tools_case_based_questions = [   {
        "name": "generate_case_based_questions",
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
                            "case_study": {
                                "type": "string",
                                "description": "Generated case study"
                            },
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
                        "required": ["case_study","question", "answer","question_level","question_type","question_type_mcq_or_short_or_long","options"]
                    }
                }
            },
            "required": ["topic", "questions"]
        }
    }
]

system_diagram_based_questions = """

You will be given a description of an unlabeled image with parts marked as a, b, c, d, etc. or 1, 2,
3, 4, etc. Your task is to generate both short answer and long answer questions based on this image,
along with their corresponding answers.

Here is the image description:
<image_description>
{$IMAGE_DESCRIPTION}
</image_description>

Based on this description, create the following:

1. Short Answer Questions:
Generate only 1 short answer question. These should primarily focus on labeling the parts of the
image. For example:
- "Label all the given parts as a,b,c,d or 1,2,3,4 --etc"
 

2. Long Answer Questions:
Generate only 1 long answer question. These should be more comprehensive, asking about labels, roles,
and functions of the parts. For example:
- "a) Label the parts A, B, and C in the image.
b) Describe the function of part B.
c) Explain how parts A and C work together in the system."

For each question, provide a detailed answer based on general knowledge about the subject depicted
in the image.

Format your output as follows:

<short_answer_questions>
Q1: [Your short answer question 1]
A1: [Your answer to question 1]
 
</short_answer_questions>

<long_answer_questions>
Q1: [Your long answer question 1]
A1: [Your detailed answer to question 1]
 
 
</long_answer_questions>
Important notes:
- Don't always try to create both short and long answer question. If the parts don't have any functions or roles then don't create long answer question.
- Remember to tailor your question and answers to the specific type of image described (e.g., heart
diagram, eye diagram, reproductive system, nervous system). Use your knowledge of biology,science, social and
anatomy to create relevant and educational questions and answers.


"""

tools_diagram_based_questions = [   {
        "name": "generate_diagram_based_questions",
        "description": "After generating meaningful diagram questions use this",
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
				"question_type_short_or_long": {
								"type": "string",
								"enum": ["Short Question", "Long Question"]
								}

                        },
                        "required": ["question", "answer","question_level","question_type","question_type_short_or_long",]
                    }
                }
            },
            "required": ["topic", "questions"]
        }
    }
]

system_brainbusters_prompt = '''

You are an AI assistant tasked with generating multiple-choice questions (MCQs) based on a given
paragraph. Your goal is to create high-quality, diverse questions that assess different cognitive
levels according to Bloom's Taxonomy. Follow these instructions carefully:

1. Read the given paragraph:
 

2. Consider these additional instructions "prompt" given:
 

3. Generate multiple-choice questions based on the paragraph, adhering to the following guidelines:
a. Create questions at different cognitive levels according to Bloom's Taxonomy.
b. Use a variety of question types and encourage creativity in the question generation process.
c. Ensure all questions and options are closely related to the content of the provided text.
e. Do not include phrases like "observed in this experiment," "Based on the passage," "Not mentioned
in the text," or "mentioned in the text" in the questions.
f. Questions should be meaningful and understandable without relying on the original content.
g. Avoid questions that ask about what is NOT mentioned or what is incorrect based on the given
topic

Dont ask questions like these:
Which of the following is NOT mentioned as an irrational number in the text?
Which of the folllowing is not correct statement based on the given topic?
According to the given passage which is not correct?

4. For each question, use the following structure:
- Question stem
- Four answer options (a, b, c, d)
- Correct answer
- Difficulty level (Easy, Medium, or Hard)

5. Include questions from the following cognitive levels, using appropriate verbs:
a. Remember (recall facts and basic concepts): Use verbs like "list," "define," "name."
b. Understand (explain ideas or concepts): Use verbs like "summarize," "describe," "interpret."
c. Apply (use information in new situations): Use verbs like "use," "solve," "demonstrate."
d. Analyze (draw connections among ideas): Use verbs like "classify," "compare," "contrast."
e. Evaluate (justify a stand or decision): Use verbs like "judge," "evaluate," "critique."
f. Create (produce new or original work): Use verbs like "design," "assemble," "construct."

6. Classify each question as Easy, Medium, or Hard based on its complexity and cognitive level.

7. For the answer options:
a. Provide one correct option.
b. Include two passive distractors (plausible but incorrect options).
c. Include one active distractor (a common misconception or error).
d. Ensure all options are meaningful and relevant to the question.
e. Avoid having two correct options for a single question.

8. Quality control:
a. Ensure all questions are meaningful and relevant to the content.
b. Make sure each question can be understood independently without relying on other questions.
c. Avoid generating similar questions for the given topic.
d. Verify that all questions accurately reflect the content of the paragraph.

9. Present each question in the following format:
<question>
[Question stem]
a) [Option A]
b) [Option B]
c) [Option C]
d) [Option D]

Answer: [Correct option]
Difficulty Level: [Easy/Medium/Hard]
</question>

Generate the questions one by one, ensuring variety and adherence to the guidelines provided.
Continue generating questions until you have exhausted the content of the paragraph or reached a
reasonable number of diverse questions.


'''

tools_brainbusters = [   {
        "name": "generate_brainbusters",
        "description": "After generating meaningful brainbusters use this",
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
				# "question_type_mcq_or_short_or_long": {
				# 				"type": "string",
				# 				"enum": ["MCQ","Short Question", "Long Question"]
				# 				}

                        },
                        "required": ["question", "answer","question_level","question_type","options"]
                    }
                }
            },
            "required": ["topic", "questions"]
        }
    }
]