import zmq
import threading

def broker():
    context = zmq.Context()


    text_frontend = context.socket(zmq.XSUB)
    text_backend = context.socket(zmq.XPUB)
    text_frontend.bind("tcp://:5560")
    text_backend.bind("tcp://:5557")


    audio_frontend = context.socket(zmq.XSUB)
    audio_backend = context.socket(zmq.XPUB)
    audio_frontend.bind("tcp://:5561")
    audio_backend.bind("tcp://:5558")


    video_frontend = context.socket(zmq.XSUB)
    video_backend = context.socket(zmq.XPUB)
    video_frontend.bind("tcp://:5562")
    video_backend.bind("tcp://:5559")

    print("Broker de mensagens iniciado.")

    def proxy(frontend, backend):
        zmq.proxy(frontend, backend)

    threading.Thread(target=proxy, args=(text_frontend, text_backend)).start()
    threading.Thread(target=proxy, args=(audio_frontend, audio_backend)).start()
    threading.Thread(target=proxy, args=(video_frontend, video_backend)).start()

if __name__ == "__main__":
    broker()