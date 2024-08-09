from dotenv import load_dotenv
import openai
import os

load_dotenv()

client = openai.OpenAI(api_key=os.environ.get('CHATGPT_API_KEY'),
)


def chatgpt_response(prompt):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,

            }
        ],
        model="gpt-4o-mini"
    )
    response_dict = response.choices
    if response_dict and len(response_dict) > 0:
        prompt_response = response_dict[0].message.content
    return prompt_response
