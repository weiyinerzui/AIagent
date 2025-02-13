import google.generativeai as genai
import os
import re
import json
import time
import tenacity
from google.api_core.exceptions import ResourceExhausted  # Import ResourceExhausted


# 配置 Gemini API 密钥
if "GEMINI_API_KEY" not in os.environ:
    raise EnvironmentError("Please set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 配置 Gemini 模型 (您可以在这里配置 generation_config 和 safety_settings)
generation_config = genai.GenerationConfig(
    temperature=0.1,
    max_output_tokens=1000000,  # 根据需要调整
)
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

# 在模块级别创建模型实例
model = genai.GenerativeModel(model_name="gemini-2.0-pro-exp-02-05",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


@tenacity.retry(
    wait=tenacity.wait_random_exponential(min=1, max=60),
    stop=tenacity.stop_after_attempt(6),
    retry=tenacity.retry_if_exception_type(ResourceExhausted)
)
def llm_call(prompt: str, system_prompt: str = "", model_name="gemini-2.0-pro-exp-02-05") -> str:
    """
    Calls the Gemini model with the given prompt and returns the response.
    Implements exponential backoff retries to handle 429 errors.
    """
    prompt_content = system_prompt + "\n" + prompt if system_prompt else prompt

    try:
        response = model.generate_content(prompt_content)
        if response.text:
            return response.text
        else:
            if response.prompt_feedback:
                print(f"Prompt feedback: {response.prompt_feedback}")
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.finish_reason != "STOP":
                        print(f"Candidate finish reason: {candidate.finish_reason}")
            return "Gemini model failed to generate a valid response."

    except ResourceExhausted as e:
        print(f"Rate limit exceeded (ResourceExhausted). Retrying...")
        raise  # Re-raise the exception to trigger tenacity retry.

    except Exception as e:  # Catch other exceptions as well
        print(f"An unexpected error occurred: {e}")
        return f"Error calling Gemini API: {e}"


def extract_json_route(text: str) -> dict:
    """
    尝试从文本中提取 JSON 格式的路由选择信息 (reasoning 和 selection)。
    如果解析失败，则返回包含错误信息的字典。
    """
    # First try: direct JSON parsing
    try:
        json_response = json.loads(text)
        if "reasoning" in json_response and "selection" in json_response:
            return {
                "reasoning": json_response["reasoning"],
                "selection": json_response["selection"]
            }
    except json.JSONDecodeError:
        pass

    # Second try: extract JSON from code blocks
    json_block_patterns = [
        r'```\s*?(?:json)?\s*?({[\s\S]*?})\s*?```',  # Standard code block
        r'{[\s\S]*?}',  # Bare JSON object
    ]
    
    for pattern in json_block_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                # Clean up the JSON string
                json_str = re.sub(r'[\u200b\ufeff\u200c]', '', json_str)  # Remove zero-width spaces
                json_str = json_str.strip()
                json_response = json.loads(json_str)
                
                if "reasoning" in json_response and "selection" in json_response:
                    return {
                        "reasoning": json_response["reasoning"],
                        "selection": json_response["selection"]
                    }
            except (json.JSONDecodeError, IndexError):
                continue

    # Third try: attempt to extract fields directly using regex
    reasoning_pattern = r'"reasoning"\s*:\s*"([^"]*)"'
    selection_pattern = r'"selection"\s*:\s*"([^"]*)"'
    
    reasoning_match = re.search(reasoning_pattern, text)
    selection_match = re.search(selection_pattern, text)
    
    if reasoning_match and selection_match:
        return {
            "reasoning": reasoning_match.group(1),
            "selection": selection_match.group(1)
        }

    # If all attempts fail, return error
    return {
        "error": "Could not extract valid JSON with reasoning and selection fields.",
        "raw_text": text[:200] + "..." if len(text) > 200 else text  # Include part of raw text for debugging
    }