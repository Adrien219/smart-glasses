import time

class AIAssistant:
    def __init__(self, voice_assistant):
        self.voice_assistant = voice_assistant
        self.last_question_time = 0
        self.question_cooldown = 10  # secondes entre les questions

    def process_question(self, question):
        """Traiter une question de l'utilisateur"""
        current_time = time.time()
        
        if current_time - self.last_question_time < self.question_cooldown:
            return "Veuillez attendre avant de poser une autre question"
        
        self.last_question_time = current_time
        
        # Questions simples prédéfinies
        question_lower = question.lower()
        
        if "qui est" in question_lower or "reconnais" in question_lower:
            return "Je peux reconnaître les personnes si elles sont dans ma base de données"
        
        elif "quoi" in question_lower or "objet" in question_lower:
            return "Je peux détecter les objets autour de vous comme les personnes, chaises, voitures, etc."
        
        elif "texte" in question_lower or "lire" in question_lower:
            return "Je peux lire le texte visible devant vous"
        
        elif "aide" in question_lower or "que peux-tu" in question_lower:
            return "Je peux reconnaître les objets, les visages, lire du texte, vous aider à naviguer et répondre à vos questions"
        
        elif "navigation" in question_lower or "déplacer" in question_lower:
            return "Utilisez le joystick pour vous déplacer. Je vous préviendrai des obstacles"
        
        else:
            return "Je suis votre assistant pour les lunettes intelligentes. Je peux reconnaître les objets, les visages et lire du texte"

    def ask_question(self, question):
        """Poser une question à l'assistant IA"""
        response = self.process_question(question)
        self.voice_assistant.speak(response)
        return response