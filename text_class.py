import zmq
import threading

class TextClient:
    def __init__(self, username):
        self.username = username
        self.context = zmq.Context()
        self.setup_connections()

    def setup_connections(self):
        # Socket para enviar mensagens (PUB)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.connect("tcp://:5560")
        print("Conectado ao publisher no endereço tcp://:5560")

        # Socket para receber mensagens (SUB)
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://:5557")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        print("Conectado ao subscriber no endereço tcp://:5557")

    def receive_messages(self, callback):
        def receive():
            while True:
                try:
                    message = self.subscriber.recv_string()
                    user, msg = message.split(':', 1)
                    print(f"Mensagem recebida: {user}: {msg}")
                    if user != self.username:
                        callback(f"{user}: {msg}")
                except Exception as e:
                    print(f"Erro ao receber mensagem: {e}")
        threading.Thread(target=receive, daemon=True).start()

    def send_message(self, message):
        full_message = f"{self.username}: {message}"
        print(f"Enviando mensagem: {full_message}")
        self.publisher.send_string(full_message)

    def notify_connection(self):
        notification = f"Sistema: {self.username} entrou na conversa."
        self.publisher.send_string(notification)

    def notify_disconnection(self):
        notification = f"Sistema: {self.username} saiu da conversa."
        self.publisher.send_string(notification)

    def disconnect(self):
        # Fechar os sockets e terminar o contexto do ZeroMQ
        try:
            self.publisher.close()
            self.subscriber.close()
            self.context.term()
            print("Desconectado e recursos liberados.")
        except Exception as e:
            print(f"Erro ao desconectar: {e}")

