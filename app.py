import cv2
import numpy as np
from mss import mss

def main():
    # Inicializamos mss para la captura de pantalla
    with mss() as sct:
        # Obtenemos los datos del monitor principal (monitor 1)
        monitor = sct.monitors[1]
        
        print("Iniciando transmisión de pantalla. Presiona 'q' para salir.")

        while True:
            # Capturamos la pantalla en formato de bytes
            screenshot = sct.grab(monitor)
            
            # Convertimos la captura a un arreglo de NumPy (formato RGB)
            img = np.array(screenshot)
            
            # Convertimos de BGRA (que usa mss/opencv internamente) a BGR estándar para OpenCV
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Opcional: Redimensionar la ventana si es muy grande (ej. al 50% de su tamaño)
            # frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            # Mostramos el fotograma en una ventana llamada "Mi Escritorio"
            cv2.imshow("Mi Escritorio", frame)

            # Esperamos 1 milisegundo y verificamos si se presionó la tecla 'q' para salir
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Cerramos todas las ventanas abiertas por OpenCV
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()