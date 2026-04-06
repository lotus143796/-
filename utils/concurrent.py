from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def run_parallel(func, items, max_workers=4, desc="Processing"):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(func, item): item for item in items}
        for future in tqdm(as_completed(future_to_item), total=len(items), desc=desc):
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"error": str(e)})
    return results