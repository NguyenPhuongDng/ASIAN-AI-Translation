import requests
from config import Config


class MNT_Service:
    def __init__(self):
        self.NGROK_URL = Config.NGROK_URL

    def call_ngrok_model(self, text: str, src_code, fr_code):
        if not self.NGROK_URL:
            return "Lỗi: NGROK_URL không được cấu hình"
        try:
            response = requests.post(f"{self.NGROK_URL}/generate", json={"prompt": text, "src":src_code, "fr":fr_code})
            if response.status_code == 200:
                data = response.json()         
                return data.get("response", "").strip()
            else:
                return f"Lỗi HTTP {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            return f"Lỗi: Không thể kết nối đến server {self.NGROK_URL}"
        except requests.exceptions.Timeout:
            return "Lỗi: Timeout khi kết nối đến server"
        except Exception as e:
            return f"Lỗi: {str(e)}"
        

MNT = MNT_Service()

