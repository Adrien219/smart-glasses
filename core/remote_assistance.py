import socket
import threading
import json
import time
from datetime import datetime

class RemoteAssistance:
    def __init__(self, voice_assistant, arduino_comm):
        self.voice_assistant = voice_assistant
        self.arduino_comm = arduino_comm
        self.server_socket = None
        self.client_socket = None
        self.is_running = False
        self.assistant_thread = None
        
        # Configuration
        self.host = '0.0.0.0'
        self.port = 8888
        
    def start_server(self):
        """Démarrer le serveur d'assistance à distance"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            self.is_running = True
            self.assistant_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.assistant_thread.start()
            
            print(f"🔄 Serveur assistance démarré sur le port {self.port}")
            self.voice_assistant.speak("Système d'assistance à distance activé")
            
        except Exception as e:
            print(f"❌ Erreur démarrage serveur: {e}")

    def _accept_connections(self):
        """Accepter les connexions entrantes"""
        while self.is_running:
            try:
                print("🔍 En attente de connexion d'assistance...")
                self.client_socket, client_address = self.server_socket.accept()
                print(f"✅ Connexion établie avec {client_address}")
                
                self.voice_assistant.speak("Connexion d'assistance établie")
                self.arduino_comm.start_buzzer(500, 1000)
                
                # Thread pour gérer la communication
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(self.client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    print(f"❌ Erreur acceptation connexion: {e}")

    def _handle_client(self, client_socket, client_address):
        """Gérer la communication avec le client"""
        try:
            while self.is_running and client_socket:
                # Recevoir des commandes
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                self._process_remote_command(data, client_socket)
                
        except Exception as e:
            print(f"❌ Erreur gestion client: {e}")
        finally:
            client_socket.close()
            print(f"🔌 Connexion avec {client_address} fermée")
            self.voice_assistant.speak("Connexion d'assistance terminée")

    def _process_remote_command(self, command, client_socket):
        """Traiter les commandes distantes"""
        try:
            data = json.loads(command)
            cmd_type = data.get('type')
            
            print(f"📨 Commande distante: {cmd_type}")
            
            if cmd_type == 'emergency_help':
                self._handle_emergency_help(data)
            elif cmd_type == 'get_status':
                self._send_status(client_socket)
            elif cmd_type == 'change_mode':
                self._change_mode(data.get('mode'))
            elif cmd_type == 'speak_message':
                self._speak_message(data.get('message'))
            elif cmd_type == 'get_camera_frame':
                self._send_camera_frame(client_socket)
                
        except json.JSONDecodeError:
            print("❌ Commande JSON invalide")

    def _handle_emergency_help(self, data):
        """Gérer une demande d'aide d'urgence"""
        helper_name = data.get('helper_name', 'Un proche')
        message = data.get('message', '')
        
        alert_msg = f"Aide demandée par {helper_name}. {message}"
        print(f"🆘 ALERTE: {alert_msg}")
        
        # Alertes multiples
        self.voice_assistant.speak(alert_msg, priority=True)
        self.arduino_comm.start_vibration(2000)
        self.arduino_comm.start_buzzer(1000, 800)

    def _send_status(self, client_socket):
        """Envoyer le statut du système"""
        status = {
            'type': 'status_update',
            'timestamp': datetime.now().isoformat(),
            'battery_level': '85%',  # À implémenter
            'current_mode': 'navigation',
            'is_connected': True
        }
        
        try:
            client_socket.send(json.dumps(status).encode('utf-8'))
        except:
            pass

    def _change_mode(self, mode):
        """Changer le mode depuis l'assistance distante"""
        if mode in ['navigation', 'object', 'face', 'text', 'ai']:
            # Implémenter le changement de mode
            self.voice_assistant.speak(f"Mode changé en {mode} par assistance distante")

    def _speak_message(self, message):
        """Faire parler le système avec un message distant"""
        if message:
            self.voice_assistant.speak(message, priority=True)

    def _send_camera_frame(self, client_socket):
        """Envoyer une frame caméra (simplifié)"""
        # À implémenter avec la caméra réelle
        status = {
            'type': 'camera_frame',
            'message': 'Fonctionnalité à implémenter'
        }
        
        try:
            client_socket.send(json.dumps(status).encode('utf-8'))
        except:
            pass

    def request_help(self, helper_phone):
        """Demander de l'aide à un proche"""
        help_message = {
            'type': 'help_request',
            'user_id': 'smart_glasses_user',
            'timestamp': datetime.now().isoformat(),
            'message': 'L\'utilisateur demande de l\'aide',
            'location': 'Position à récupérer'  # À implémenter avec GPS
        }
        
        print(f"🆘 Demande d'aide envoyée à {helper_phone}")
        self.voice_assistant.speak("Demande d'aide envoyée")

    def stop_server(self):
        """Arrêter le serveur"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        print("🔴 Serveur assistance arrêté")