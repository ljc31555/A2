import requests

def check_comfyui_status(url="http://127.0.0.1:8188"):
    try:
        # 使用与ComfyUI客户端相同的代理配置
        proxies = {}
        if "127.0.0.1" in url or "localhost" in url:
            # 本地地址绕过代理
            proxies = {
                'http': None,
                'https': None
            }
        
        response = requests.get(url, timeout=5, proxies=proxies)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

        print(f"Successfully connected to {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print("First 500 characters of response content:")
        print(response.text[:500])

        if "text/html" not in response.headers.get('Content-Type', ''):
            print("Warning: Content-Type is not text/html. This might be the cause of the JavaScript error.")
        if "<html" not in response.text.lower():
            print("Warning: Response does not appear to be a full HTML page.")

    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to ComfyUI at {url}. Please ensure ComfyUI is running and accessible.")
        print(f"Details: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Error: Connection to ComfyUI at {url} timed out.")
        print(f"Details: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred while connecting to ComfyUI at {url}.")
        print(f"Details: {e}")

if __name__ == "__main__":
    check_comfyui_status()