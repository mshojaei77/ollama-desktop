class ChatbotManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_chatbots = {}
        return cls._instance

    def add_chatbot(self, chatbot_id: int, name: str):
        self.active_chatbots[chatbot_id] = {"name": name, "status": "active"}

    def get_chatbots(self):
        return self.active_chatbots
    
    def get_chatbot(self, chatbot_id: int):
        return self.active_chatbots.get(chatbot_id)
    
    def delete_chatbot(self, chatbot_id: int):
        del self.active_chatbots[chatbot_id]
    
    def cleanup_all_chatbots(self):
        for chatbot_id in self.active_chatbots:
            self.cleanup_chatbot(chatbot_id)
            del self.active_chatbots[chatbot_id]
        
        