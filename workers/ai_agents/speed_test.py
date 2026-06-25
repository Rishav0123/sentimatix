import os
import time
import json
import shutil
import subprocess
import httpx

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Candidate models to benchmark
CANDIDATE_MODELS = [
    {"name": "qwen2.5:1.5b", "label": "Qwen 2.5 (1.5B)", "pull_size": "986 MB"},
    {"name": "qwen2.5:3b", "label": "Qwen 2.5 (3B)", "pull_size": "1.9 GB"},
    {"name": "llama3.2:latest", "label": "Llama 3.2 (3B)", "pull_size": "2.0 GB"},
    {"name": "qwen2.5:7b", "label": "Qwen 2.5 (7B)", "pull_size": "4.7 GB"},
]

def find_ollama_executable():
    """Find ollama path dynamically or default to localappdata on Windows."""
    path = shutil.which("ollama")
    if path:
        return path
    
    # Check default Windows AppData location
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        default_win = os.path.join(appdata, "Programs", "Ollama", "ollama.exe")
        if os.path.exists(default_win):
            return default_win
            
    return "ollama"

def get_installed_models():
    """Query local Ollama instance for currently loaded/installed models."""
    try:
        resp = httpx.get("http://localhost:11434/api/tags")
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []

def pull_model(model_name):
    """Pull the model using the Ollama CLI."""
    ollama_cli = find_ollama_executable()
    print(f"[PULL] Pulling '{model_name}' (this may take a minute if not cached)...")
    try:
        # Run subprocess with utf-8 encoding and replace errors to avoid cp1252 charmap decode issues
        process = subprocess.Popen(
            [ollama_cli, "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace"
        )
        # Stream the output so the user sees the progress bar
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Remove extra trailing spaces/newlines and strip non-ASCII characters to prevent cp1252 print crashes
                line = output.strip()
                clean_line = line.encode('ascii', 'ignore').decode('ascii').strip()
                if clean_line:
                    print(f"  {clean_line[:75]}", end="\r")
        process.wait()
        print(f"\n[SUCCESS] Successfully pulled '{model_name}'")
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to pull '{model_name}' via CLI: {e}")
        return False

def run_benchmark(model_name):
    """Run a structured news sentiment analysis request on the model and record metrics."""
    sample_title = "ICICI Bank stock (INE090A01021): March quarter profit rises on loan growth"
    sample_content = "ICICI Bank stock (INE090A01021): March quarter profit rises on loan growth. Consolidated profit rose 17.4% to Rs 10,707 crore from Rs 9,122 crore in the same period last year. Loan growth was strong at 16.8% YoY."
    sample_stock = "ICICI Bank"

    prompt = f"""Determine the financial sentiment for {sample_stock}.
News: Title: {sample_title}\nContent: {sample_content}

Return JSON: {{"sentiment": "positive"|"negative"|"neutral"|"conflicted", "score": float, "confidence": float}}"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        },
        "format": "json"
    }

    print(f"[TEST] Testing {model_name}...")
    
    # Warmup Run (ensures model is loaded in memory so we measure inference, not just load time)
    try:
        httpx.post(OLLAMA_API_URL, json=payload, timeout=60.0)
    except Exception as e:
        print(f"[WARNING] Warmup run failed: {e}")
        return None

    # Benchmark Run
    start_time = time.time()
    try:
        response = httpx.post(OLLAMA_API_URL, json=payload, timeout=60.0)
        total_wall_time = time.time() - start_time
        response.raise_for_status()
        
        data = response.json()
        
        # Ollama returns timing metadata in nanoseconds
        total_duration = data.get("total_duration", 0) / 1e9
        load_duration = data.get("load_duration", 0) / 1e9
        prompt_eval_duration = data.get("prompt_eval_duration", 0) / 1e9
        eval_duration = data.get("eval_duration", 0) / 1e9
        eval_count = data.get("eval_count", 0)
        
        tokens_per_second = eval_count / eval_duration if eval_duration > 0 else 0
        
        # Parse result to check JSON structure
        result_content = data.get("response", "")
        
        return {
            "wall_time": round(total_wall_time, 2),
            "load_time": round(load_duration, 2),
            "eval_time": round(eval_duration, 2),
            "eval_count": eval_count,
            "tps": round(tokens_per_second, 2),
            "response": result_content.strip()
        }
    except Exception as e:
        print(f"[ERROR] Benchmark execution failed: {e}")
        return None

def main():
    print("=" * 60)
    print("      SENTIMATIX LOCAL OLLAMA BENCHMARK SUITE")
    print("=" * 60)

    installed = get_installed_models()
    print(f"Installed models detected: {installed}\n")

    results = []

    for model_info in CANDIDATE_MODELS:
        name = model_info["name"]
        label = model_info["label"]
        
        # Ensure model is pulled
        is_pulled = False
        for inst in installed:
            if inst.startswith(name):
                is_pulled = True
                break
                
        if not is_pulled:
            print(f"Model '{label}' is not downloaded.")
            # We pull the smaller models dynamically
            success = pull_model(name)
            if not success:
                print(f"Skipping {label} due to pull failure.\n")
                continue
        else:
            print(f"'{label}' already installed. Proceeding to benchmark...")

        # Run benchmark
        metrics = run_benchmark(name)
        if metrics:
            print(f"   Wall Time: {metrics['wall_time']}s | Generation Speed: {metrics['tps']} Tokens/sec")
            print(f"   Response: {metrics['response']}\n")
            results.append({
                "label": label,
                "size": model_info["pull_size"],
                "wall_time": f"{metrics['wall_time']}s",
                "eval_time": f"{metrics['eval_time']}s",
                "eval_count": metrics["eval_count"],
                "tps": f"{metrics['tps']} Tok/s",
                "output": metrics["response"]
            })
        else:
            print(f"[ERROR] Failed benchmark for {label}\n")

    # Print Final Summary Table
    print("\n" + "=" * 60)
    print("                     FINAL RESULTS TABLE")
    print("=" * 60)
    print(f"{'Model':<20} | {'Disk Size':<10} | {'Gen Time':<10} | {'Tokens':<8} | {'Speed':<12}")
    print("-" * 70)
    for r in results:
        print(f"{r['label']:<20} | {r['size']:<10} | {r['eval_time']:<10} | {r['eval_count']:<8} | {r['tps']:<12}")
    print("=" * 60)
    print("\n*Note: 'Gen Time' represents pure generation time. Wall time includes context evaluation and networking.")

if __name__ == "__main__":
    main()
