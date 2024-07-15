import zmq
import pyaudio
import threading
import time
import uuid

# Configurações de áudio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class AudioClient:
    def __init__(self):
        self.client_id = str(uuid.uuid4())  # Gerar um identificador único para o cliente
        self.context = zmq.Context()
        self.setup_connections()
        self.audio = pyaudio.PyAudio()
        self.running = False

    def setup_connections(self):
        # Socket para enviar áudio (PUB)
        self.audio_publisher = self.context.socket(zmq.PUB)
        self.audio_publisher.connect("tcp://:5561")
        print("Socket PUB de áudio conectado.")

        # Socket para receber áudio (SUB)
        self.audio_subscriber = self.context.socket(zmq.SUB)
        self.audio_subscriber.connect("tcp://:5558")
        self.audio_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        print("Socket SUB de áudio conectado.")

    def receive_audio(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        print("Stream de áudio de saída configurado.")
        while self.running:
            try:
                message = self.audio_subscriber.recv_string()
                sender_id, data = message.split('|', 1)
                if sender_id != self.client_id:
                    stream.write(data.encode('latin1'))
                    print("Áudio recebido")
            except Exception as e:
                print(f"Erro ao receber áudio: {e}")
                time.sleep(1)
        stream.close()

    def send_audio(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Stream de áudio de entrada configurado.")
        while self.running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                message = f"{self.client_id}|{data.decode('latin1')}"
                self.audio_publisher.send_string(message)
                print("Áudio enviado")
            except Exception as e:
                print(f"Erro ao capturar ou enviar áudio: {e}")
                time.sleep(1)
        stream.close()

    def start(self):
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_audio, daemon=True)
        self.send_thread = threading.Thread(target=self.send_audio, daemon=True)
        self.receive_thread.start()
        self.send_thread.start()

    def stop(self):
        self.running = False
        self.receive_thread.join()
        self.send_thread.join()
        print("Transmissão de áudio parada.")