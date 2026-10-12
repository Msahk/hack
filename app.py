import base64
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Variable global para almacenar el último fotograma recibido
latest_frame = ""

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cloud Screen Share</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            h1 { margin-bottom: 25px; font-weight: 600; color: #38bdf8; text-align: center; }
            .menu-card { background: #1e293b; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4); text-align: center; max-width: 400px; width: 90%; }
            .btn { display: block; width: 100%; padding: 14px 20px; margin: 12px 0; background: #2563eb; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: background 0.2s; box-sizing: border-box; }
            .btn:hover { background: #1d4ed8; }
            .btn-viewer { background: #059669; }
            .btn-viewer:hover { background: #047857; }
        </style>
    </head>
    <body>
        <div class="menu-card">
            <h1>Cloud Stream Bridge</h1>
            <a class="btn" href='/sender'>Transmitir desde este dispositivo</a>
            <a class="btn btn-viewer" href='/viewer'>Ver Transmisión (PC)</a>
        </div>
    </body>
    </html>
    """

@app.route('/sender')
def sender():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Emisor de Pantalla</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }
            .card { background: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4); max-width: 400px; width: 90%; }
            h2 { color: #38bdf8; margin-top: 0; }
            .btn { padding: 14px 24px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s; width: 100%; margin-top: 15px; }
            .btn-start { background: #059669; color: white; }
            .btn-start:hover { background: #047857; }
            .btn-stop { background: #dc2626; color: white; display: none; } /* Oculto inicialmente con display: none */
            .btn-stop:hover { background: #b91c1c; }
            #status { margin-top: 15px; font-size: 14px; color: #94a3b8; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Panel Emisor</h2>
            <p id="status">Estado: En espera de iniciar</p>
            
            <!-- Botón para iniciar -->
            <button id="startBtn" class="btn btn-start">Iniciar Transmisión</button>
            
            <!-- Botón oculto inicialmente con display: none que al hacer clic desactiva la transmisión -->
            <button id="stopBtn" class="btn btn-stop">Detener Transmisión</button>
        </div>

        <video id="video" autoplay playsinline style="display:none;"></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const statusText = document.getElementById('status');

            let mediaStream = null;
            let intervalId = null;

            startBtn.onclick = async () => {
                try {
                    // Nota: Por seguridad estricta de los navegadores móviles, la primera vez requiere 
                    // un toque en este botón para autorizar el uso de la pantalla.
                    mediaStream = await navigator.mediaDevices.getDisplayMedia({ 
                        video: { frameRate: 10, width: { ideal: 1280 }, height: { ideal: 720 } },
                        audio: false 
                    });
                    
                    video.srcObject = mediaStream;
                    
                    // Ocultar botón de inicio y mostrar el botón de detener
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'block';
                    statusText.textContent = "Estado: Transmitiendo en vivo...";
                    statusText.style.color = "#10b981";

                    // Enviar fotogramas al servidor cada segundo
                    intervalId = setInterval(() => {
                        if (!mediaStream || !mediaStream.active) return;
                        canvas.width = video.videoWidth / 2;
                        canvas.height = video.videoHeight / 2;
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        
                        const dataURL = canvas.toDataURL('image/jpeg', 0.5);
                        
                        fetch('/upload', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ image: dataURL })
                        }).catch(err => console.error("Error al enviar frame:", err));
                    }, 1000);

                    // Si el usuario detiene la transmisión desde la barra nativa del navegador móvil
                    mediaStream.getVideoTracks()[0].onended = () => {
                        stopTransmission();
                    };

                } catch (err) {
                    console.error("Error al compartir pantalla:", err);
                    statusText.textContent = "Estado: Cancelado o denegado.";
                    statusText.style.color = "#ef4444";
                }
            };

            // Acción del botón oculto para desactivar la transmisión al hacer clic
            stopBtn.onclick = () => {
                stopTransmission();
            };

            function stopTransmission() {
                if (mediaStream) {
                    mediaStream.getTracks().forEach(track => track.stop());
                    mediaStream = null;
                }
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
                video.srcObject = null;
                
                // Revertir interfaz
                stopBtn.style.display = 'none';
                startBtn.style.display = 'block';
                statusText.textContent = "Estado: Transmisión detenida.";
                statusText.style.color = "#94a3b8";
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/upload', methods=['POST'])
def upload():
    global latest_frame
    data = request.get_json()
    if data and 'image' in data:
        latest_frame = data['image']
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/viewer')
def viewer():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visor de Pantalla</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0f19; color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; text-align: center; }
            h2 { color: #38bdf8; margin-bottom: 10px; }
            .screen-container { background: #1e293b; padding: 20px; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); display: inline-block; max-width: 90%; }
            img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }
            #status { margin-top: 12px; font-size: 14px; color: #94a3b8; font-weight: 500; }
        </style>
    </head>
    <body>
        <h2>Monitoreo en Tiempo Real</h2>
        <div class="screen-container">
            <!-- No solicita permisos de cámara ni audio en el visor -->
            <img id="screen" alt="Esperando señal de transmisión..." src="" />
            <div id="status">Conectando...</div>
        </div>

        <script>
            const imgElement = document.getElementById('screen');
            const statusDiv = document.getElementById('status');

            // Comienza automáticamente al abrir la página sin requerir ninguna interacción ni permisos
            setInterval(async () => {
                try {
                    const response = await fetch('/get_frame');
                    const data = await response.json();
                    if (data.image) {
                        imgElement.src = data.image;
                        statusDiv.textContent = "Estado: Transmitiendo en vivo";
                        statusDiv.style.color = "#10b981";
                    } else {
                        statusDiv.textContent = "Estado: Esperando al dispositivo emisor...";
                        statusDiv.style.color = "#f59e0b";
                    }
                } catch (e) {
                    statusDiv.textContent = "Estado: Error de conexión con el servidor.";
                    statusDiv.style.color = "#ef4444";
                }
            }, 1000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/get_frame')
def get_frame():
    global latest_frame
    return jsonify({"image": latest_frame})

if __name__ == '__main__':
    app.run(debug=True)