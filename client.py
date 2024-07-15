import tkinter as tk
import zmq
import cv2
import threading
import numpy as np
from PIL import Image, ImageTk
from tkinter import scrolledtext, messagebox
from text_class import TextClient
from audio_class import AudioClient

# Inicializando as variáveis globais do client
video_index = []  # Armazena o índice de cada usuário para o vídeo
image_list = [None] * 4  # Lista para armazenar objetos ImageTk.PhotoImage
text_client = None
userid = None
context = None  # Contexto global para o ZeroMQ
subscribe_running = False  # Flag para controlar a execução do subscriber


# Funções de vídeo
def get_camera():
    # Busca uma câmera virtual disponível ou uma segunda câmera caso a primeira esteja ocupada
    for j in range(20):
        cap = cv2.VideoCapture(j)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Câmera disponível encontrada no índice {j}")
                cap.release()
                return j
    return 0

def subscribe_video(socket):
    global userid, image_list, video_index, subscribe_running

    while subscribe_running:
        try:
            # Recebendo do broker a imagem e seu user_id e decodificando
            message = socket.recv_multipart()
            rcvd_user_id, frame = message
            rcvd_user_id = rcvd_user_id.decode('utf-8')

            npimg = np.frombuffer(frame, dtype=np.uint8)
            img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)

            # Encontra ou adiciona o usuário na lista de índices
            if rcvd_user_id not in video_index:
                for i in range(len(video_index)):
                    if video_index[i] is None:
                        video_index[i] = rcvd_user_id
                        break
                else:
                    video_index.append(rcvd_user_id)

            # Encontra o índice do usuário na lista de índices
            try:
                index = video_index.index(rcvd_user_id)
                image_list[index] = imgtk  # Atualiza a imagem na lista correta
            except ValueError:
                print(f"Usuário '{rcvd_user_id}' não encontrado em video_index")

        except zmq.error.ContextTerminated:
            break  # Encerra o loop se o contexto do ZeroMQ for terminado
        except Exception as e:
            print(f"Erro ao receber vídeo: {e}")


def publish_video(socket):
    global userid

    index = get_camera()
    cap = cv2.VideoCapture(index)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Não pode receber frame. Saindo ...")
            break
        _, buffer = cv2.imencode('.jpg', frame)
        socket.send_multipart([userid.encode('utf-8'), buffer.tobytes()])
        print('Enviado')
    cap.release()

def start_text_client():
    global text_client, userid
    userid = username_entry.get()
    if not userid:
        messagebox.showerror("Erro", "Nome de usuário não pode ser vazio!")
        return

    text_client = TextClient(userid)

    def update_chat_window(message):
        chat_window.config(state=tk.NORMAL)  # Habilita a edição temporariamente
        chat_window.insert(tk.END, f"{message}\n")
        chat_window.see(tk.END)
        chat_window.config(state=tk.DISABLED)  # Desabilita a edição novamente

    text_client.receive_messages(update_chat_window)

    def send_text_message(event=None):
        message = message_entry.get()
        if message:
            text_client.send_message(message)
            chat_window.config(state=tk.NORMAL)  # Habilita a edição temporariamente
            chat_window.insert(tk.END, f"Você: {message}\n")
            chat_window.see(tk.END)
            chat_window.config(state=tk.DISABLED)  # Desabilita a edição novamente
            message_entry.delete(0, tk.END)

    send_button.config(command=send_text_message)
    message_entry.bind('<Return>', send_text_message)

    messagebox.showinfo("Conexão", "Cliente conectado. Pronto para enviar mensagens.")

def start_audio_client():
    global audio_client
    audio_client = AudioClient()
    audio_client.start()
    messagebox.showinfo("Conexão", "Áudio conectado e funcionando.")

def stop_audio_client():
    global audio_client
    if audio_client:
        audio_client.stop()
        messagebox.showinfo("Conexão", "Áudio desconectado.")


# Função para iniciar os clientes de vídeo
def start_video_client():
    global userid, context, subscribe_running

    userid = username_entry.get()
    if not userid:
        messagebox.showerror("Erro", "Nome de usuário não pode ser vazio!")
        return

    context = zmq.Context()

    publisher = context.socket(zmq.PUB)
    publisher.connect(f"tcp://:5562")

    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f"tcp://:5559")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    subscribe_running = True
    threading.Thread(target=subscribe_video, args=(subscriber,)).start()

    print("Pronto para receber vídeo.")

    # Inicia a publicação de vídeo em uma nova thread
    threading.Thread(target=publish_video, args=(publisher,)).start()

    print("Pronto para enviar vídeo.")


# Função para parar os clientes de vídeo
def stop_video_client():
    global context, subscribe_running

    subscribe_running = False  # Define a flag para parar a execução do subscribe_video
    for j in range(len(image_list)):
        image_list[j] = None
    messagebox.showinfo("Conexão", "Vídeo desconectado.")


def atualizar_imagens():
    # Aqui você atualiza image_list com novas imagens conforme necessário
    for i in range(len(image_list)):
        if image_list[i]:
            label_list[i].config(image=image_list[i])
    app.after(1, atualizar_imagens)


def on_closing():
    global text_client, context
    if context:
        context.term()

    app.destroy()


# Interface Tkinter
app = tk.Tk()
app.title("Cliente de Comunicação")

# Seção de texto
text_frame = tk.Frame(app)
text_frame.pack(padx=10, pady=10)

username_label = tk.Label(text_frame, text="Usuário:")
username_label.pack(side=tk.LEFT)
username_entry = tk.Entry(text_frame)
username_entry.pack(side=tk.LEFT)

connect_button = tk.Button(text_frame, text="Conectar", command=start_text_client)
connect_button.pack(side=tk.LEFT)

chat_window = scrolledtext.ScrolledText(text_frame, width=50, height=20)
chat_window.pack(pady=10)
chat_window.config(state=tk.DISABLED)  # Desabilita a edição inicialmente

message_entry = tk.Entry(text_frame, width=40)
message_entry.pack(side=tk.LEFT, padx=5)
send_button = tk.Button(text_frame, text="Enviar")
send_button.pack(side=tk.LEFT)

# Botões para iniciar e parar áudio
audio_button = tk.Button(text_frame, text="Iniciar Áudio", command=start_audio_client)
audio_button.pack(side=tk.LEFT, padx=5)

stop_audio_button = tk.Button(text_frame, text="Parar Áudio", command=stop_audio_client)
stop_audio_button.pack(side=tk.LEFT, padx=5)

# Seção de vídeo
video_frame = tk.Frame(app)
video_frame.pack(padx=10, pady=10)

# Configurando as labels de vídeo e botões de controle conforme o trecho fornecido
label_list = []

for i in range(4):
    label = tk.Label(video_frame, image=None)
    label.grid(row=0, column=i % 4)
    label_list.append(label)
    # Configura a coluna para redimensionar conforme necessário
    app.grid_columnconfigure(i, weight=1)

    # Pode haver uma demora para renderizar as câmeras seguintes conectadas ao sistema

# Botões para iniciar e parar vídeo
video_button = tk.Button(text_frame, text="Iniciar Vídeo", command=start_video_client)
video_button.pack(side=tk.LEFT, padx=5)

stop_video_button = tk.Button(text_frame, text="Parar Vídeo", command=stop_video_client)
stop_video_button.pack(side=tk.LEFT, padx=5)

# Inicia a função de atualização de imagens
app.after(1, atualizar_imagens)  # Atualiza a cada 10 milissegundos (0.01 segundo)

app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()