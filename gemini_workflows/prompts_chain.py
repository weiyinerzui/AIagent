from typing import List, Dict, Callable
import os
from util import llm_call

# proxy settings
os.environ['http_proxy'] = 'http://127.0.0.1:10809'
os.environ['https_proxy'] = 'http://127.0.0.1:10809'
os.environ['all_proxy'] = 'socks5://127.0.0.1:10809'


def chain(input: str, prompts: List[str]) -> str:
    """链式调用 LLM，在步骤间传递结果"""
    result = input
    for i, prompt in enumerate(prompts, 1):
        print(f"\nStep:{i}")
        result = llm_call(f"{prompt}\nInput:{result}")  # 后面的 result 由前一步 result + prompt 生成
        print(result) 
    return result

# example: 结构化提取文本中的内容，并格式化输出
# 逐步将原始文本格式化为 Markdown 表格

data_processing_steps = [
    """Extract only numeric values and their associated metric from the text.
    Fromat each as 'value:metric' on a line.
    Example format:
    92: customer satisfaction
    45%: revenue growth
    """,

    """Convert all numerical values to percentages where possible.
    If not a percentage or points, convert to decimal (e.g., 92 points -> 92%).
    Keep one number per line.
    Example format:
    92%: customer satisfaction
    45%: revenue growth""",
    
    """Sort all lines in descending order by numerical value.
    Keep the format 'value: metric' on each line.
    Example:
    92%: customer satisfaction
    87%: employee satisfaction""",
    
    """Format the sorted data as a markdown table with columns:
    | Metric | Value |
    |:--|--:|
    | Customer Satisfaction | 92% |"""
]

report = """
Q3 Performance Summary:
Our customer satisfaction score rose to 92 points this quarter.
Revenue grew by 45% compared to last year.
Market share is now at 23% in our primary market.
Customer churn decreased to 5% from 8%.
New user acquisition cost is $43 per user.
Product adoption rate increased to 78%.
Employee satisfaction is at 87 points.
Operating margin improved to 34%.
"""


print("\nInput text:")
print(report)
formatted_report = chain(report, data_processing_steps)
print(formatted_report)
