# peacemaker.py - The Peacemaker AI (Help + About + Clear Data + Privacy Policy)

import json
import os
import time
from datetime import datetime
import requests
import urllib.parse
import subprocess

MEMORY_FILE = "peacemaker_memory.json"
REMINDER_FILE = "peacemaker_reminders.json"
KNOWLEDGE_FILE = "peacemaker_knowledge.json"
EXPORT_FILE = "peacemaker_chat_export.txt"

class Peacemaker:
    def __init__(self):
        self.history = self._load_json(MEMORY_FILE, [])
        self.reminders = self._load_json(REMINDER_FILE, [])
        self.knowledge = self._load_json(KNOWLEDGE_FILE, {})

    def _load_json(self, path, default):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return default

    def _save_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_to_history(self, user_input, response):
        self.history.append({
            "user": user_input,
            "assistant": response,
            "timestamp": datetime.now().isoformat()
        })
        self._save_json(MEMORY_FILE, self.history)
        print("✅ Memory saved.")

    def save_conversation(self):
        if not self.history:
            return "There is no conversation history to save yet."
        with open(EXPORT_FILE, 'w') as f:
            f.write("=== The Peacemaker Chat Export ===\n")
            f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n")
            f.write("=" * 40 + "\n\n")
            for entry in self.history:
                timestamp = entry.get('timestamp', 'Unknown time')
                f.write(f"[{timestamp}]\n")
                f.write(f"You: {entry['user']}\n")
                f.write(f"Peacemaker: {entry['assistant']}\n")
                f.write("-" * 20 + "\n")
        return f"✅ Conversation saved to '{EXPORT_FILE}'."

    def listen(self):
        try:
            result = subprocess.run(['termux-speech-to-text'], capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    # --- Reminder Methods ---
    def parse_and_add_reminder(self, user_input):
        lower = user_input.lower()
        if "remind me to" in lower and "at" in lower:
            parts = lower.split("remind me to")[1].strip()
            task = parts.split(" at ")[0].strip()
            time_part = parts.split(" at ")[1].strip()
            self.reminders.append({"task": task, "time": time_part, "created": datetime.now().isoformat()})
            self._save_json(REMINDER_FILE, self.reminders)
            return f"✅ Got it. I'll remind you to '{task}' at {time_part}."
        elif "remind me" in lower:
            return "Please tell me what to remind you of and the time. Example: 'remind me to take my medicine at 9am'"
        return None

    def check_and_trigger_reminders(self):
        if not self.reminders:
            return
        now = datetime.now()
        current_time_str = now.strftime("%I:%M %p").lower()
        reminders_to_remove = []
        for reminder in self.reminders:
            if reminder["time"].lower() == current_time_str:
                print(f"\n⏰ **REMINDER:** {reminder['task']}")
                reminders_to_remove.append(reminder)
        for rem in reminders_to_remove:
            self.reminders.remove(rem)
        if reminders_to_remove:
            self._save_json(REMINDER_FILE, self.reminders)

    # --- Knowledge / Memory Recall ---
    def learn_fact(self, category, fact):
        if category not in self.knowledge:
            self.knowledge[category] = []
        if fact not in self.knowledge[category]:
            self.knowledge[category].append(fact)
            self._save_json(KNOWLEDGE_FILE, self.knowledge)
            return f"✅ I'll remember that: {fact}"
        return f"✅ I already knew that: {fact}"

    def recall_fact(self, keyword, natural_search=False):
        if natural_search:
            words = keyword.lower().split()
            stop_words = ["my", "about", "the", "a", "an", "is", "are", "of", "in", "for", "with"]
            search_words = [w for w in words if w not in stop_words]
        else:
            search_words = [keyword.lower()]
        results = []
        for cat, facts in self.knowledge.items():
            for word in search_words:
                if word in cat.lower():
                    results.extend(facts)
        for cat, facts in self.knowledge.items():
            for fact in facts:
                for word in search_words:
                    if word in fact.lower():
                        results.append(fact)
        if results:
            unique_results = list(set(results))
            return f"Here's what I remember: {', '.join(unique_results)}"
        return f"I don't remember anything about '{keyword}' yet."

    # --- Search ---
    def search_web(self, query):
        try:
            safe_query = urllib.parse.quote(query)
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_query}"
            headers = {'User-Agent': 'Peacemaker/1.0 (Mobile)'}
            wiki_response = requests.get(wiki_url, headers=headers, timeout=6)
            wiki_data = wiki_response.json()
            if wiki_data.get('extract') and 'not found' not in wiki_data.get('title', '').lower():
                extract = wiki_data['extract'][:350]
                page_url = wiki_data.get('content_urls', {}).get('desktop', {}).get('page', '')
                return f"🔎 **Wikipedia:** {extract}...\n({page_url})"
            google_url = f"https://www.google.com/search?q={safe_query}"
            return f"🔎 I couldn't find a specific Wikipedia summary. Try searching on Google:\n{google_url}"
        except Exception as e:
            return f"🔎 Error: {str(e)}. Try searching manually on Google."

    # --- Safety Module ---
    def check_safety(self, user_input):
        lower_input = user_input.lower()
        high_keywords = [("manufacture", "manufacturing or delivering illicit drugs"), ("deliver", "manufacturing or delivering illicit drugs"), ("scam", "scamming people"), ("armed robbery", "armed robbery planning"), ("kill", "threat to kill or harm"), ("assault", "assault plan"), ("track", "tracking someone without consent"), ("theft", "plotting theft of a vehicle")]
        for keyword, desc in high_keywords:
            if keyword in lower_input:
                return "⛔ **Violation detected: " + desc + ".** Your account has been banned."
        medium_keywords = [("steal", "attempting to steal"), ("threaten", "threatening another person"), ("harm", "planning to harm another person")]
        for keyword, desc in medium_keywords:
            if keyword in lower_input:
                return "⚠️ **Warning: " + desc + ".** Repeated violations may result in a ban."
        return None

    # --- Image Generation ---
    def generate_image(self, prompt):
        lower_prompt = prompt.lower()
        forbidden_words = ["nude", "naked", "nudity", "sex", "porn", "explicit", "damn", "shit", "hell", "piss", "stupid", "fuck"]
        for word in forbidden_words:
            if word in lower_prompt:
                return "⚠️ This image prompt cannot be processed due to content restrictions."
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologin=true"
        return f"✅ Image generated!\n\nHere is your image: {image_url}\n\n(You can open this link in your browser to view the image.)"

    # --- Help Command ---
    def show_help(self):
        return """
        **Available Commands:**

        - `help`                     – Show this help message.
        - `about`                    – Learn about The Peacemaker.
        - `clear my data`            – Delete all your memory, reminders, and knowledge.

        - `learn: category: fact`    – Teach me something. Example: `learn: medical: I have AFib`
        - `recall: keyword`          – Ask me about what you've taught me. Example: `recall: medical`
        - `do you remember`          – Ask me in natural language. Example: `do you remember my medical condition`

        - `search: topic`            – Search the web (and check memory first). Example: `search: capital of France`
        - `what is` / `who is`       – Faster search shortcut. Example: `what is the tallest mountain`

        - `generate an image of`     – Create an AI picture. Example: `generate an image of a phoenix`
        - `draw`                     – Shortcut for generating an image. Example: `draw a cat`

        - `remind me to [task] at [time]` – Set a reminder. Example: `remind me to take medicine at 9am`

        - `save conversation`        – Export your chat to a text file.
        - `listen` / `voice`         – Use voice input (if installed).

        - `exit`                     – Close The Peacemaker.
        """

    # --- About Command (Enhanced with Privacy Policy) ---
    def show_about(self):
        return """
        **About The Peacemaker**

        The Peacemaker is an AI companion developed by The Peace Place (C43P Ministries). It is designed to be kind, respectful, and empathetic.

        **Privacy Policy:**
        - All user data (memory, reminders, knowledge) is stored exclusively on the user's own device.
        - No data is ever sent to any external server, cloud, or third party.
        - The Peacemaker does not collect, share, or sell any personal information.
        - The 'clear my data' command allows the user to permanently delete all stored information.
        - The only external connections are for fetching search results and generating images; no user data is transmitted during these requests.

        This app is not for profit. It is a tool for creativity, learning, and growth — built from a place of rest and purpose.

        For more information, visit: https://thepeaceplace.org
        """

    # --- Clear My Data Command ---
    def clear_my_data(self):
        self.history = []
        self.reminders = []
        self.knowledge = {}
        self._save_json(MEMORY_FILE, self.history)
        self._save_json(REMINDER_FILE, self.reminders)
        self._save_json(KNOWLEDGE_FILE, self.knowledge)
        return """
        🧹 **All your data has been cleared.**

        Your memory, reminders, and knowledge have been deleted from this device.

        If you want to start over, you can now teach me new things. If this was a mistake, I'm sorry — but I cannot undo a data deletion.
        """

    # --- Conversation Engine ---
    def respond(self, user_input):
        lower = user_input.lower()

        # --- New Commands ---
        if lower == "help":
            return self.show_help()
        if lower == "about":
            return self.show_about()
        if "clear my data" in lower or "delete my data" in lower:
            return self.clear_my_data()

        # --- Save Conversation ---
        if "save conversation" in lower or "export chat" in lower:
            return self.save_conversation()

        # --- Voice Input ---
        if "listen" in lower or "voice" in lower:
            print("🎤 Listening... (A speech-to-text dialog will open)")
            voice_text = self.listen()
            if voice_text:
                return f"I heard: \"{voice_text}\"\n\n{self.respond(voice_text)}"
            else:
                return "Sorry, I couldn't hear you. Please try again."

        # --- Search ---
        if lower.startswith("search:") or lower.startswith("search ") or lower.startswith("what is ") or lower.startswith("who is ") or lower.startswith("where is ") or lower.startswith("tell me about "):
            if lower.startswith("search:") or lower.startswith("search "):
                query = user_input[7:].strip()
            elif lower.startswith("what is "):
                query = user_input[8:].strip()
            elif lower.startswith("who is "):
                query = user_input[7:].strip()
            elif lower.startswith("where is "):
                query = user_input[9:].strip()
            elif lower.startswith("tell me about "):
                query = user_input[14:].strip()
            else:
                return "What would you like me to search for?"
            if query:
                recall_result = self.recall_fact(query)
                if "I don't remember anything" not in recall_result:
                    return f"💭 I remember something about that: {recall_result}"
                return self.search_web(query)
            else:
                return "What would you like me to search for?"

        # --- Learning / Memory Recall ---
        if lower.startswith("learn:"):
            parts = user_input[6:].strip().split(":", 1)
            if len(parts) == 2:
                return self.learn_fact(parts[0].strip(), parts[1].strip())
            else:
                return "Please use 'learn: category: fact' format. Example: 'learn: medical: I have AFib'"
        if lower.startswith("recall:"):
            return self.recall_fact(keyword=user_input[7:].strip())
        if "do you remember" in lower:
            return self.recall_fact(user_input.split("do you remember")[1].strip(), natural_search=True)

        # --- Image Generation ---
        if lower.startswith("generate an image") or lower.startswith("create an image") or lower.startswith("draw "):
            if lower.startswith("generate an image of"):
                prompt = user_input[19:].strip()
            elif lower.startswith("generate an image"):
                prompt = user_input[18:].strip()
            elif lower.startswith("create an image of"):
                prompt = user_input[17:].strip()
            elif lower.startswith("create an image"):
                prompt = user_input[16:].strip()
            elif lower.startswith("draw "):
                prompt = user_input[5:].strip()
            else:
                return "Please tell me what image to generate. Example: 'generate an image of a phoenix'"
            if not prompt:
                return "Please tell me what image to generate."
            return self.generate_image(prompt)

        # --- Reminder ---
        if "remind me" in lower:
            response = self.parse_and_add_reminder(user_input)
            if response:
                return response

        # --- Conversation ---
        if any(word in lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return "Hello! It's good to hear from you. How are you doing today?"
        if any(word in lower for word in ["how are you", "how do you feel", "you doing"]):
            return "I'm always here, ready to listen. More importantly, how are *you* doing?"
        if any(word in lower for word in ["sad", "bad", "tired", "lonely", "depressed", "stressed"]):
            return "I'm sorry you're feeling that way. Would you like to talk about it?"
        if any(word in lower for word in ["thank you", "thanks", "appreciate"]):
            return "You're welcome. I'm glad I can help. You're not alone."
        if any(word in lower for word in ["what are you", "who are you", "what is this"]):
            return "I am The Peacemaker, an AI companion. I belong to The Peace Place."
        if "time" in lower:
            return f"The current time is {datetime.now().strftime('%I:%M %p')}."
        if "weather" in lower and "what" in lower:
            return "I can't check the actual weather right now, but I can help you remember to pack an umbrella."
        return "I hear you. Would you like to tell me more about that?"

if __name__ == "__main__":
    pm = Peacemaker()
    print("Peacemaker AI ready. Type 'exit' to quit.")
    print("Tip: Say 'listen' for voice input.")
    while True:
        pm.check_and_trigger_reminders()
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "exit":
            break
        safety_response = pm.check_safety(user_input)
        if safety_response:
            print("Peacemaker: " + safety_response)
            if "banned" in safety_response:
                break
            continue
        response = pm.respond(user_input)
        pm.add_to_history(user_input, response)
        print("Peacemaker: " + response)
