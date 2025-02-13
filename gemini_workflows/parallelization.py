from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Callable
import os
from util import llm_call

# proxy settings
os.environ['http_proxy'] = 'http://127.0.0.1:10809'
os.environ['https_proxy'] = 'http://127.0.0.1:10809'
os.environ['all_proxy'] = 'socks5://127.0.0.1:10809'


def parallel(prompt: str, inputs: List[str], n_workers: int = 3) -> List[str]:
    """使用同一个 Prompt 同时处理多个输入"""
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(llm_call, f"{prompt}\nInput:{x}") for x in inputs]
        return [f.result() for f in futures]
    

# Example 2: 并行化处理利益相关者影响分析
# Process impact analysis for multiple stakeholder groups concurrently

stakeholders = [
    """Customers:
    - Price sensitive
    - Want better tech
    - Environmental concerns""",
    
    """Employees:
    - Job security worries
    - Need new skills
    - Want clear direction""",
    
    """Investors:
    - Expect growth
    - Want cost control
    - Risk concerns""",
    
    """Suppliers:
    - Capacity constraints
    - Price pressures
    - Tech transitions"""
]

impact_results = parallel(
    """Analyze how market changes will impact this stakeholder group.
    Provide specific impacts and recommended actions.
    Format with clear sections and priorities.""",
    stakeholders
)

for result in impact_results:
    print(result)