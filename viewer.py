import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import threading
from PIL import Image
import os

def show_video_with_frame_range_sum(sdt):
    window = tk.Toplevel()
    window.title("Просмотр каналов с диапазоном")
    window.configure(bg='black')

    top_frame = tk.Frame(window, bg='black')
    top_frame.pack(padx=10, pady=10)

    bottom_frame = tk.Frame(window, bg='black')
    bottom_frame.pack(padx=10, pady=10)

    fig, axes = plt.subplots(1, 3, figsize=(12, 6))
    fig.patch.set_facecolor('black')
    for ax in axes:
        ax.set_facecolor('black')
        ax.tick_params(colors='white')
        ax.title.set_color('white')

    canv = FigureCanvasTkAgg(fig, master=top_frame)
    canv.get_tk_widget().pack()

    total_frames = sdt.data[0].shape[2]
    center_frame = tk.IntVar(value=total_frames // 2)
    range_width = tk.IntVar(value=25)

    img_handles = [ax.imshow(np.zeros((512, 512, 3), dtype=np.uint8)) for ax in axes]
    titles = ["Канал 0 (красный)", "Канал 2 (зелёный)", "Смешанное"]

    lock = threading.Lock()
    update_pending = [False]

    def process_channel(ch, start, end):
        summed = np.zeros((512, 512), dtype=np.float32)
        for i in range(start, end + 1):
            summed += sdt.data[ch][:, :, i].astype(np.float32)
        maxz = np.max(summed)
        trhld = maxz / 20
        if trhld <= 2:
            trhld = 2
        elif trhld >= 7:
            trhld = 7
        else:
            trhld = int(trhld)
        summed[summed <= trhld] = 0
        sumz = np.sum(summed)

        norm = (summed - np.min(summed)) / (np.max(summed) - np.min(summed) + 1e-5) * 255
        channel_img = norm.astype(np.uint8)
        rgb = np.zeros((512, 512, 3), dtype=np.uint8)
        if ch == 0:
            rgb[:, :, 0] = channel_img
        else:
            rgb[:, :, 1] = channel_img
        return rgb, sumz

    def threaded_update():
        with lock:
            update_pending[0] = True

        center = center_frame.get()
        width = range_width.get()
        start = max(0, center - width // 2)
        end = min(total_frames - 1, center + width // 2)

        try:
            img_0, sum_0 = process_channel(0, start, end)
            img_2, sum_2 = process_channel(2, start, end)
            combined = np.clip(img_0.astype(np.int16) + img_2.astype(np.int16), 0, 255).astype(np.uint8)
            sum_combined = sum_0 + sum_2  # или можно пересчитать отдельно, как нужно

            img_0 = np.flip(img_0, axis=0)
            img_2 = np.flip(img_2, axis=0)
            combined = np.flip(combined, axis=0)

        except Exception as e:
            print(f"Ошибка обработки: {e}")
            img_0 = img_2 = combined = np.zeros((512, 512, 3), dtype=np.uint8)
            sum_0 = sum_2 = sum_combined = 0

        def update_gui():
            for ax, img, title, handle, value in zip(
                axes, [img_0, img_2, combined], titles, img_handles, [sum_0, sum_2, sum_combined]):
                handle.set_data(img)
                ax.set_title(f"{title}\nКадры: {start}-{end}\nСумма: {value:.0f}", color='white')
                ax.axis('off')
            canv.draw()

        window.after(0, update_gui)
        with lock:
            update_pending[0] = False

    def on_slider_release(event=None):
        if not update_pending[0]:
            threading.Thread(target=threaded_update, daemon=True).start()

    def update_center_frame(value):
        center_frame.set(int(value))
        center_slider.set(center_frame.get())
        on_slider_release()

    def update_range_width(event=None):
        try:
            val = int(width_entry.get())
            if val > 0:
                range_width.set(val)
                on_slider_release()
        except:
            pass

    style = ttk.Style()
    style.configure("TScale", troughcolor='gray20', background='gray80')

    def save_mask():
        center = center_frame.get()
        width = range_width.get()
        start = max(0, center - width // 2)
        end = min(total_frames - 1, center + width // 2)

        try:
            frames = [sdt.data[2][:, :, i].astype(np.float32) for i in range(start, end + 1)]
            summed = np.sum(frames, axis=0)
            averaged = summed / (end - start + 1)
            averaged = np.flip(averaged, axis=0)

            gray = np.clip(averaged, 0, 255).astype(np.uint8)
            threshold = 2
            mask = (gray < threshold).astype(np.uint8) * 255

            im = Image.fromarray(mask)
            im.save(os.path.join(os.path.dirname(sdt.filename), "mask.png"))
            print("Маска сохранена")
        except Exception as e:
            print(f"Ошибка при сохранении маски: {e}")

    from tkinter import filedialog
    import pickle  # или другой способ чтения файла, если это .sdt

    def open_new_file():
        file_path = filedialog.askopenfilename(filetypes=[("SDT files", "*.sdt"), ("All files", "*.*")])
        if not file_path:
            return

        try:
            # 👇 Заменить на твой способ загрузки данных:
            with open(file_path, "rb") as f:
                new_sdt = pickle.load(f)  # или другой метод

            # Обновляем глобальный sdt
            nonlocal sdt, total_frames
            sdt = new_sdt
            total_frames = sdt.data[0].shape[2]

            center_frame.set(total_frames // 2)
            center_slider.config(to=total_frames - 1)
            center_slider.set(center_frame.get())
            center_entry.delete(0, tk.END)
            center_entry.insert(0, str(center_frame.get()))

            threaded_update()

        except Exception as e:
            print(f"Не удалось загрузить файл: {e}")

    ttk.Label(bottom_frame, text="Центральный кадр", background='black', foreground='white').pack()
    center_slider_frame = tk.Frame(bottom_frame, bg='black')
    center_slider_frame.pack(pady=5)

    center_slider = ttk.Scale(center_slider_frame, from_=0, to=total_frames - 1, variable=center_frame,
                              orient="horizontal", length=600)
    center_slider.pack(side="left")

    center_entry = ttk.Entry(center_slider_frame, width=6, justify="center")
    center_entry.insert(0, str(center_frame.get()))
    center_entry.pack(side="left", padx=5)
    center_entry.bind("<Return>", lambda event: update_center_frame(center_entry.get()))

    range_frame = tk.Frame(bottom_frame, bg='black')
    range_frame.pack(pady=5)
    tk.Label(range_frame, text="Ширина диапазона:", bg='black', fg='white').pack(side="left")
    width_entry = ttk.Entry(range_frame, width=6, justify="center", textvariable=range_width)
    width_entry.pack(side="left")
    width_entry.bind("<Return>", update_range_width)

    save_button = tk.Button(bottom_frame, text="Сохранить маску", command=save_mask, bg='gray20', fg='white')
    save_button.pack(pady=10)

    center_slider.bind("<ButtonRelease-1>", on_slider_release)

    open_button = tk.Button(bottom_frame, text="Открыть другой файл", command=open_new_file, bg='gray20', fg='white')
    open_button.pack(pady=5)

    threading.Thread(target=threaded_update, daemon=True).start()
    window.mainloop()
