import tkinter as tk
from tkinter import ttk
import threading
import time
from collections import deque
from constants import constantes
from dashboard_render import leer_serial, conectar_arduino
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from assistant_webhook import estado


# --------- configuraciones generales para la interfaz ----------
root = tk.-Tk()
root.title("Dashboard Arduino")
root.geometry("1000x640")
root.configure(bg="#e6f2ff")

# ============== Indicadores graficos ==============
# 1. Sensor de temperatura
frame_left = tk.Frame(root, bg="#e6f2ff")
frame_left.pack(side="left", fill="y", padx=12, pady=12)

frame_temp = tk.LabelFrame(frame_left, text="Temperatura", padx=8, pady=8)
frame_temp.pack(pady=6)

canvas_temp = tk.Canvas(frame_temp, width=60, height=200, bg="#222")
canvas_temp.pack()
lbl_temp = ttk.Label(frame_temp, text="Temperatura: -- °C", font=("Arial", 10))
lbl_temp.pack(pady=6)

# Dibujar el termometro con un canvas
canvas_temp.create_rectangle(20, 10, 40, 190, outline="white", width=2)
termometro_barra = canvas_temp.create_rectangle(20, 190, 40, 190, fill="red")

# 2. Humedad
frame_hum = tk.LabelFrame(frame_left, text="Humedad", padx=8, pady=8)
frame_hum.pack(pady=6)

lbl_hum = ttk.Label(frame_hum, text="Humedad: -- %", font=("Arial", 10))
lbl_hum.pack(pady=6)
canvas_hum = tk.Canvas(frame_hum, width=200, height=30, bg="#333")
canvas_hum.pack()
hum_barra = canvas_hum.create_rectangle(0, 0, 0, 30, fill="blue")

# 3. Día / Noche
frame_day = tk.LabelFrame(frame_left, text="Día / Noche", padx=8, pady=8)
frame_day.pack(pady=6)

lbl_dia = ttk.Label(frame_day, text="Día/Noche: --", font=("Arial", 10))
lbl_dia.pack()
lbl_icono = ttk.Label(frame_day, text="?", font=("Arial", 36))
lbl_icono.pack(pady=4)

# 4. Puerta
frame_puerta = tk.LabelFrame(frame_left, text="Puerta", padx=8, pady=8)
frame_puerta.pack(pady=6)

lbl_puerta = ttk.Label(frame_puerta, text="Puerta: --", font=("Arial", 10))
lbl_puerta.pack()
canvas_puerta = tk.Canvas(frame_puerta, width=100, height=200, bg="#222")
canvas_puerta.pack(pady=6)
# Puerta rect
puerta_rect = canvas_puerta.create_rectangle(10, 10, 90, 190, fill="#663300")

# 5. Log
frame_log = tk.Frame(root, bg="#e6f2ff")
frame_log.pack(side="bottom", fill="x", padx=8, pady=8)
txt_log = tk.Text(frame_log, height=8)
txt_log.pack(fill="x")

# ============== Gráficas en tiempo real ==============
frame_charts = tk.Frame(root, bg="#e6f2ff")
frame_charts.pack(side="right", fill="both", expand=True, padx=8, pady=8)

fig = Figure(figsize=(6,5), dpi=100)
ax_temp = fig.add_subplot(311)
ax_hum = fig.add_subplot(312)
ax_ldr = fig.add_subplot(313)

# datos (deque con maxlen)
MAX_POINTS = 60
temps = deque(maxlen=MAX_POINTS)
hums = deque(maxlen=MAX_POINTS)
ldrs = deque(maxlen=MAX_POINTS)

chart_canvas = FigureCanvasTkAgg(fig, master=frame_charts)
chart_canvas.get_tk_widget().pack(fill="both", expand=True)

# ---------- Parser / Aplicador de paquetes ----------
current_packet = {}  # recoge claves hasta '---' separador

def apply_packet(packet):
    """Aplica el paquete ya completo a la UI (llamado desde hilo via root.after)."""
    # temperatura
    if "TEMP" in packet:
        try:
            t = float(packet["TEMP"])
            lbl_temp.config(text=f"Temperatura: {t:.1f} °C")
            # actualizar termómetro (0..50 -> pixel coords)
            y = 190 - int((t / 50.0) * 180)
            if y < 10: y = 10
            if y > 190: y = 190
            canvas_temp.coords(termometro_barra, 20, y, 40, 190)
            estado["temperatura"] = t
            temps.append(t)
        except:
            pass

    # humedad
    if "HUM" in packet:
        try:
            h = float(packet["HUM"])
            lbl_hum.config(text=f"Humedad: {h:.0f} %")
            ancho = int((h / 100.0) * 200)
            if ancho < 0: ancho = 0
            if ancho > 200: ancho = 200
            canvas_hum.coords(hum_barra, 0, 0, ancho, 30)
            estado['humedad'] = h
            hums.append(h)
        except:
            pass

    # ldr
    if "LDR" in packet:
        try:
            l = int(packet["LDR"])
            ldrs.append(l)
        except:
            pass

    # daynight
    if "DAYNIGHT" in packet:
        v = packet["DAYNIGHT"].strip().upper()
        if v in ("NIGHT","NOCHE"):
            lbl_dia.config(text="Día/Noche: NOCHE")
            lbl_icono.config(text="🌝") # emoji lo saque de wahs app
            estado["dia_noche"] = "noche"
        else:
            lbl_dia.config(text="Día/Noche: DIA")
            lbl_icono.config(text="☀️") # emoji sacado de whatsapp
            estado["dia_noche"] = 'dia'

    # door
    if "DOOR" in packet:
        v = packet["DOOR"].strip().upper()
        if v == "OPEN":
            lbl_puerta.config(text="Puerta: ABIERTA")
            # mover rect (abrir hacia la izquierda)
            canvas_puerta.coords(puerta_rect, 10, 10, 50, 190)
            estado['puerta'] = 'abierta'
        else:
            lbl_puerta.config(text="Puerta: CERRADA")
            canvas_puerta.coords(puerta_rect, 10, 10, 90, 190)
            estado["puerta"] = 'cerrada'

    # motion -> we can briefly log it
    if "MOTION" in packet:
        try:
            m = int(packet["MOTION"])
            if m:
                txt_log.insert(tk.END, "Movimiento detectado (MOTION=1)\n")
                txt_log.see(tk.END)
        except:
            pass

    # actualizar graficas
    actualizar_charts()

def actualizar_charts():
    """Dibuja las curvas actuales."""
    ax_temp.clear()
    ax_temp.plot(list(temps))
    ax_temp.set_ylabel("°C")
    ax_temp.set_title("Temperatura")

    ax_hum.clear()
    ax_hum.plot(list(hums))
    ax_hum.set_ylabel("%")
    ax_hum.set_title("Humedad")

    ax_ldr.clear()
    ax_ldr.plot(list(ldrs))
    ax_ldr.set_ylabel("LDR")
    ax_ldr.set_title("LDR (analog)")

    fig.tight_layout()
    chart_canvas.draw()

# ---------- Lector de serial en hilo ----------
# El lector agrupa líneas hasta encontrar '---', entonces aplica el paquete.
lock = threading.Lock()

def process_line(line):
    """Procesa una sola linea de entrada. Construye paquete y al encontrar '---' lo aplica."""
    global current_packet
    if not line:
        return

    # si leer_serial retorna lista (modo simulación), lo gestionamos fuera para iterar cada elemento
    if isinstance(line, (list, tuple)):
        for ln in line:
            process_line(ln)
        return

    # normalizar
    ln = line.strip()
    # logear
    txt_log.insert(tk.END, ln + "\n")
    txt_log.see(tk.END)

    # Si separador
    if ln == "---":
        # aplicar paquete (usar copy para evitar race)
        pkt = current_packet.copy()
        current_packet = {}
        # gui update must run in main thread
        root.after(0, apply_packet, pkt)
        return

    # parse KEY:VALUE lines (TEMP:24.5, HUM:60, ...)
    if ":" in ln:
        parts = ln.split(":", 1)
        key = parts[0].strip().upper()
        val = parts[1].strip()
        current_packet[key] = val
    else:
        # si línea no tiene ':', la guardamos en log pero también comprobamos palabras
        # por ejemplo "NOCHE" o "DIA" (compatibilidad)
        up = ln.upper()
        if up in ("NOCHE", "NIGHT", "DIA", "DAY"):
            current_packet["DAYNIGHT"] = "NIGHT" if "N" in up else "DAY"
        elif "ABR" in up:
            current_packet["DOOR"] = "OPEN"
        elif "CERR" in up:
            current_packet["DOOR"] = "CLOSED"
        # else lo ignoramos

def hilo_lectura():
    """Hilo que llama a leer_serial() y procesa resultado."""
    while True:
        try:
            line = leer_serial()
            if line:
                process_line(line)
            else:
                time.sleep(0.05)
        except Exception as e:
            # loguear errores y reintentar
            txt_log.insert(tk.END, f"ERROR LECTURA: {e}\n")
            txt_log.see(tk.END)
            time.sleep(0.5)

# iniciamos hilo lector
thread = threading.Thread(target=hilo_lectura, daemon=True)
thread.start()

def heartbeat():
    root.after(500, heartbeat)

root.after(500, heartbeat)
root.mainloop()