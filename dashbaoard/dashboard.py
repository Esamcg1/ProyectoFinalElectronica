import tkinter as tk
from tkinter import ttk
import serial
import threading
import time
import math
from constants import constantes
from dashboard_render import leer_serial, conectar_arduino
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ---------- configuraciones generales para la interfaz ----------
root = tk.Tk()
root.title("Dashboard Arduino")
root.geometry("900x600")
root.configure(bg="lightblue")

# ============== Indicadores graficos ==============

# 1. Sensor de temperatura
frame_temp = tk.Frame(root)
frame_temp.pack(side="left", padx=20)

canvas_temp = tk.Canvas(frame_temp, width=60, height=200, bg="#222")
canvas_temp.pack()
lbl_temp = ttk.Label(frame_temp, text="Temperatura: -- °C")
lbl_temp.pack(pady=5)

# Dibujar el termometro con un canvas
canvas_temp.create_rectangle(20, 10, 40, 190, outline="white", width=2)
termometro_barra = canvas_temp.create_rectangle(20, 190, 40, 190, fill="red")

# leer la humedad del sensor de temperatura
frame_hum = tk.Frame(root)
frame_hum.pack(side="left", padx=20)

lbl_hum = ttk.Label(frame_hum, text="Humedad: -- %")
lbl_hum.pack(pady=5)
canvas_hum = tk.Canvas(frame_hum, width=200, height=30, bg="#333")
canvas_hum.pack()
hum_barra = canvas_hum.create_rectangle(0, 0, 0, 30, fill="blue")

# 3. Sensores de luz, iconos para el dia y lanoche
frame_dia = tk.Frame(root)
frame_dia.pack(side="left", padx=20)

lbl_dia = ttk.Label(frame_dia, text="Día/Noche: --")
lbl_dia.pack()
lbl_icono = ttk.Label(frame_dia, text="?", font=("Arial", 40))
lbl_icono.pack()

# 4. Leer los datos de la puerta y animar
frame_puerta = tk.Frame(root)
frame_puerta.pack(side="left", padx=30)

lbl_puerta = ttk.Label(frame_puerta, text="Puerta: --")
lbl_puerta.pack()

canvas_puerta = tk.Canvas(frame_puerta, width=80, height=200, bg="#222")
canvas_puerta.pack()
# Puerta cerrada 
puerta_rect = canvas_puerta.create_rectangle(10, 10, 70, 190, fill="#663300")


# ============== LOGS==============
txt_log = tk.Text(root, height=12, width=110)
txt_log.pack(side="bottom", pady=10)

# ============== Lecturas en timepp real ==============

frame_charts = tk.Frame(root)
frame_charts.pack(side="right")

fig = Figure(figsize=(4,4))
ax_temp = fig.add_subplot(311)
ax_hum = fig.add_subplot(312)
ax_ldr = fig.add_subplot(313)

temps = []
hums = []
ldrs = []

chart_canvas = FigureCanvasTkAgg(fig, master=frame_charts)
chart_canvas.get_tk_widget().pack()

def actualizar_charts():
    if len(temps) > 50:
        temps.pop(0)
        hums.pop(0)
        ldrs.pop(0)

    ax_temp.clear()
    ax_temp.plot(temps)
    ax_temp.set_title("Temperatura")

    ax_hum.clear()
    ax_hum.plot(hums)
    ax_hum.set_title("Humedad")

    ax_ldr.clear()
    ax_ldr.plot(ldrs)
    ax_ldr.set_title("LDR")

    chart_canvas.draw()


# -------------- Ffuncion para el parseo --------------
def actualizar_dashboard(linea):
    txt_log.insert(tk.END, linea + "\n")
    txt_log.see(tk.END)

    # ----- Temperatura y Humedad -----
    if "T:" in linea and "H:" in linea:
        try:
            t = float(linea.split("T:")[1].split(" ")[0])
            h = float(linea.split("H:")[1].split(" ")[0])
            lbl_temp.config(text=f"Temperatura: {t} °C")
            lbl_hum.config(text=f"Humedad: {h} %")

            # Actualizar el sensor o termometro de temperatura (0°C = abajo, 50°C = arriba)
            y = 190 - int((t / 50) * 180)
            canvas_temp.coords(termometro_barra, 20, y, 40, 190)

            # Actualizar barra de humedad (0-100%)
            ancho = int((h / 100) * 200)
            canvas_hum.coords(hum_barra, 0, 0, ancho, 30)

            temps.append(t)
            hums.append(h)
            actualizar_charts()
        except:
            pass

    # ----- Día/Noche -----
    if "NOCHE" in linea:
        lbl_dia.config(text="Día/Noche: NOCHE")
        lbl_icono.config(text="🌙")
    elif "DIA" in linea:
        lbl_dia.config(text="Día/Noche: DIA")
        lbl_icono.config(text="🌞")

    # ----- Puerta -----
    if "Abriendo puerta" in linea:
        lbl_puerta.config(text="Puerta: ABIERTA")
        canvas_puerta.coords(puerta_rect, 10, 10, 40, 190)

    if "Cerrando puerta" in linea or "cerrada" in linea:
        lbl_puerta.config(text="Puerta: CERRADA")
        canvas_puerta.coords(puerta_rect, 10, 10, 70, 190)

    # ----- LDR -----
    if "LDR" in linea or "Dia" in linea or "NOCHE" in linea:
        try:
            # el Arduino no imprime el valor LDR directamente
            pass
        except:
            pass


# -------------- HILO LECTOR --------------
def hilo_lectura():
    while True:
        linea = leer_serial()
        if linea:
            actualizar_dashboard(linea)

thread = threading.Thread(target=hilo_lectura, daemon=True)
thread.start()

root.mainloop()