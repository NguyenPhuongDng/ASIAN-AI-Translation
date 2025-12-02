import google.generativeai as genai
from config import Config

import sqlite3
import ahocorasick
# from comet import download_model, load_from_checkpoint
import requests


class Gemini_Service:
    def __init__(self):
        print("Initializing Style Service...")
        try:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
            self.DB_PATH = Config.DB_PATH
            print("Gemini Model Initialized.")
        except Exception as e:
            print(f"[ERROR] Could not initialize Gemini model: {e}")
            self.model = None

        self.NGROK_URL = Config.NGROK_URL
        self.GEN_TRANSLATE_CONFIG = {
            "temperature": 1,
            "top_p": 1.0,
            "top_k": 40,
            "max_output_tokens": 4048,
        }


    def call_gemini_style_edit(self, src_text: str, tranlate_text: str, source_lang : str, target_lang : str, style: str, prompt_template) -> str:
        prompt = prompt_template.get(style, "None")
        if prompt == "None":
            return tranlate_text

        prompt_filled = prompt.replace("{{source_text}}", src_text).replace("{{translated_text}}", tranlate_text).replace("{{source_lang}}", source_lang).replace("{{target_lang}}", target_lang)

        #print(f"[Thinking] Style Prompt: {prompt_filled}")
        response = self.model.generate_content(
            prompt_filled,
            generation_config=self.GEN_TRANSLATE_CONFIG
        )
        after_text = response.text.strip()
        return after_text

    def load_terms_for_automaton(self, source_lang, target_lang):
        conn = sqlite3.connect(Config.DB_PATH)
        # Lấy dữ liệu gốc
        rows = conn.execute(f'''
            SELECT "{source_lang}", "{target_lang}"
            FROM dict
            WHERE "{source_lang}" != '' AND "{target_lang}" != ''
        ''').fetchall()
        conn.close()
        return rows


    # =========================
    # 3️⃣ Build automaton (Key là chữ thường, Value giữ nguyên gốc)
    # =========================
    def build_automaton(self, term_pairs):
        A = ahocorasick.Automaton()
        for src, tgt in term_pairs:
            if src:
                # Key add vào Automaton PHẢI là chữ thường để match case-insensitive
                # Value lưu lại (src_gốc, tgt_gốc) để trả về kết quả đẹp
                A.add_word(src.lower(), (src, tgt)) 
        A.make_automaton()
        return A


    # =========================
    # 4️⃣ Query (SỬA LỖI LOGIC QUAN TRỌNG: Word Boundary)
    # =========================
    def query_terms_in_sentence(self, sentence, automaton):
        sentence_lower = sentence.lower()
        results = []
        
        # Hàm kiểm tra ký tự có phải là chữ/số không
        def is_word_char(char):
            return char.isalnum() or char == '_'

        # Aho-Corasick trả về end_index (vị trí ký tự cuối cùng của từ match)
        for end_idx, (original_src, original_tgt) in automaton.iter(sentence_lower):
            matched_len = len(original_src)
            start_idx = end_idx - matched_len + 1
            
            # 1. Kiểm tra biên trái (ký tự trước từ tìm thấy)
            if start_idx > 0 and is_word_char(sentence_lower[start_idx - 1]):
                continue # Bỏ qua vì dính vào từ trước (vd: match "ba" trong "sân_banh")

            # 2. Kiểm tra biên phải (ký tự sau từ tìm thấy)
            if end_idx < len(sentence_lower) - 1 and is_word_char(sentence_lower[end_idx + 1]):
                continue # Bỏ qua vì dính vào từ sau (vd: match "cat" trong "cation")

            # Nếu vượt qua 2 check trên -> Đây là từ nguyên vẹn
            results.append({
                "start": start_idx,
                "end": end_idx,
                "source_match": original_src, # Từ gốc trong từ điển
                "target": original_tgt,       # Nghĩa gốc
                "in_sentence": sentence[start_idx:end_idx+1] # Từ thực tế trong câu (giữ case của câu)
            })
            
        return results

    def make_prompt(self, src_text: str, src_lang: str, tar_lang: str, tar_text : str, phrases: str, k : int, style: str) -> str:
        prompt = f"""
    You are a post-editing model. Your task is to refine and correct a target sentence (tar_text) based on:
    1. The original source sentence (src_text)
    2. The languages involved (src_lang → tar_lang)
    3. A list of key phrases extracted from the source text
    4. The requirement to preserve semantic accuracy while improving fluency, coherence, and correctness in tar_lang.

    Given:
    - src_text: "{src_text}"
    - src_lang: "{src_lang}"
    - tar_text: "{tar_text}"
    - tar_lang: "{tar_lang}"
    - extracted_phrases: {phrases}
    - style: {style}

    Objective:
    - Adjust tar_text so it accurately reflects the meaning of src_text.
    - Ensure all extracted phrases are correctly represented or translated in tar_text.
    - Improve grammar, coherence, and naturalness in tar_lang.
    - Do NOT alter meaning unless needed to correct errors.
    - Create improved {k} tar_text, each tar_text is on its own line
    **Only show tar_text, no additional information including the number at the beginning of the line**
    """ 
        return prompt

    def commet_score(self, data, src_text, tar_text):
        if not self.NGROK_URL:
            return None

        # build payload
        payload = []
        for candidate in data:
            payload.append({
                "src": [src_text],
                "mt": [candidate],
                "ref": [[tar_text]]
            })

        try:
            response = requests.post(
                f"{self.NGROK_URL}/comet",
                json={"data": payload}
            )
            comet = response.json().get("comet_score", None)
            if comet is None:
                return None

        except Exception:
            return None
        
        # comet is now a list of scores, e.g. [0.91, 0.83, 0.77]
        best_index = max(range(len(comet)), key=lambda i: comet[i])
        
        best_sentence = data[best_index]
        best_score = comet[best_index]

        return best_sentence, best_score


        
    def call_gemini_edit(self, src_text: str, src_lang: str, tar_lang: str, tar_text: str, style : str, prompt_template, thinking : bool) -> str:
        if not thinking:
            results = self.call_gemini_style_edit(
                src_text,
                tar_text,
                src_lang,
                tar_lang,
                style,
                prompt_template
            )
            return results
                
        if not self.model: return tar_text

        term_pairs = self.load_terms_for_automaton(src_lang, tar_lang)
        automaton = self.build_automaton(term_pairs)
        # 2. Query
        matched_terms = self.query_terms_in_sentence(src_text, automaton)
        phrases = [f"{m['in_sentence']} -> {m['target']}" for m in matched_terms]
        #print(f"[Thinking] Found {len(phrases)} terms to preserve: {phrases}")
        # 3. Prompt
        prompt = self.make_prompt(src_text, src_lang, tar_lang, tar_text, phrases, k=5, style=style)
        print(f"[Thinking] Prompt: {prompt}")
        try:
            # SỬA LỖI: generate_content
            response = self.model.generate_content(
                prompt,
                generation_config=self.GEN_TRANSLATE_CONFIG
            )
            
            # SỬA LỖI: .scrip() -> .strip()
            candidates = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            
            if len(candidates) > 1:
                best_sentence, best_score = self.commet_score(candidates, src_text, tar_text)
                if not best_sentence:
                    return tar_text
                return best_sentence
            elif len(candidates) == 1:
                return candidates[0]
            else:
                return tar_text

        except Exception as e:
            print(f"[Thinking Error] type={type(e)}, detail={e}")
            return tar_text

gemini_service = Gemini_Service()