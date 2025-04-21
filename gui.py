import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import imageio.v2 as imageio
from main import process_frames, create_six_panel_video, turn_sdt
import webbrowser

channels = {0: "red", 2: "green"}


def ask_file_path():
    return filedialog.askopenfilename(
        title="Выберите .sdt файл",
        filetypes=[("SDT files", "*.sdt"), ("All files", "*.*")]
    )


def update_progress(value):
    progress_bar["value"] = value
    root.update_idletasks()


def choose_file():
    file_path = ask_file_path()
    path_entry.delete(0, tk.END)
    path_entry.insert(0, file_path)


def make_loop_video(filename):
    reader = imageio.get_reader(filename)
    frames = [frame for frame in reader]
    reader.close()
    all_frames = frames + frames[::-1]
    loop_filename = filename.replace('.mp4', '_loop.mp4')
    writer = imageio.get_writer(loop_filename, fps=25)
    for frame in all_frames:
        writer.append_data(frame)
    writer.close()
    return loop_filename


def run_processing():
    try:
        update_progress(0)
        file_path = path_entry.get()
        file_name = os.path.basename(file_path)
        file_stem = os.path.splitext(file_name)[0]

        base_dir = os.path.dirname(file_path)
        output_dir = os.path.join(base_dir, "video_cells", file_stem)
        os.makedirs(output_dir, exist_ok=True)

        sdt = turn_sdt(file_path)
        fps = float(fps_entry.get())
        k = {0: float(k0_entry.get()), 2: float(k2_entry.get())}

        if var_normal.get():
            output_text.insert(tk.END, "Создание обычных видео...\n")
            output_text.see(tk.END)
            process_frames(sdt, k, channels, fps, accumulate=False,
                           suffix="_обычное", filename_label=file_name,
                           progress_callback=lambda p: update_progress(p * 0.25),
                           output_dir=output_dir)
            output_text.insert(tk.END, "Обычные видео готовы.\n")
            output_text.see(tk.END)

        if var_accum.get():
            output_text.insert(tk.END, "Создание видео с накоплением...\n")
            output_text.see(tk.END)
            process_frames(sdt, k, channels, fps, accumulate=True,
                           suffix="_необычное", filename_label=file_name,
                           progress_callback=lambda p: update_progress(25 + p * 0.25),
                           output_dir=output_dir)
            output_text.insert(tk.END, "Видео с накоплением готовы.\n")
            output_text.see(tk.END)

        if var_sixpanel.get():
            output_text.insert(tk.END, "Создание 6-панельного видео...\n")
            output_text.see(tk.END)
            create_six_panel_video((2048, 1536), fps, output_dir,
                                   progress_callback=lambda p: update_progress(50 + p * 0.25))
            output_text.insert(tk.END, "6-панельное видео готово.\n")
            output_text.see(tk.END)

        if var_loop.get():
            output_text.insert(tk.END, "Создание цикличных видео...\n")
            output_text.see(tk.END)
            files_to_loop = []

            if var_normal.get():
                files_to_loop += [f"channel_0_обычное.mp4", f"channel_2_обычное.mp4", f"combined_video_обычное.mp4"]
            if var_accum.get():
                files_to_loop += [f"channel_0_необычное.mp4", f"channel_2_необычное.mp4", f"combined_video_необычное.mp4"]
            if var_sixpanel.get():
                files_to_loop.append("six_panel_video.mp4")

            for file in files_to_loop:
                full_path = os.path.join(output_dir, file)
                looped = make_loop_video(full_path)
                output_text.insert(tk.END, f"Создано цикличное видео: {looped}\n")
                output_text.see(tk.END)

        output_text.insert(tk.END, f"=== Все задачи завершены ===\nВидео в папке: {output_dir}\n")
        output_text.see(tk.END)
        update_progress(100)

        if open_folder_after.get():
            webbrowser.open(f'file://{output_dir}')

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        output_text.insert(tk.END, f"Ошибка: {e}\n")
        output_text.see(tk.END)


def start_thread():
    thread = threading.Thread(target=run_processing)
    thread.start()


# === GUI ===
root = tk.Tk()
root.title("Обработка SDT-видео")
root.geometry("700x700")

select_file_button = tk.Button(root, text="Выбрать файл", command=choose_file)
start_button = tk.Button(root, text="Начать обработку", command=start_thread)

path_entry = tk.Entry(root, width=60)
fps_entry = tk.Entry(root, width=10)
k0_entry = tk.Entry(root, width=10)
k2_entry = tk.Entry(root, width=10)

output_text = tk.Text(root, height=15, width=85)
progress_bar = ttk.Progressbar(root, length=600, mode='determinate')

fps_entry.insert(0, "25")
k0_entry.insert(0, "1")
k2_entry.insert(0, "1")

# Чекбоксы
var_normal = tk.BooleanVar(value=True)
var_accum = tk.BooleanVar(value=True)
var_sixpanel = tk.BooleanVar(value=True)
var_loop = tk.BooleanVar(value=False)
open_folder_after = tk.BooleanVar(value=True)

tk.Label(root, text="FPS:").place(x=20, y=10)
fps_entry.place(x=60, y=10)

tk.Label(root, text="k0:").place(x=130, y=10)
k0_entry.place(x=160, y=10)

tk.Label(root, text="k2:").place(x=230, y=10)
k2_entry.place(x=260, y=10)

path_entry.place(x=20, y=40)
select_file_button.place(x=520, y=36)

tk.Checkbutton(root, text="Обычные видео", variable=var_normal).place(x=20, y=80)
tk.Checkbutton(root, text="С накоплением", variable=var_accum).place(x=160, y=80)
tk.Checkbutton(root, text="6 панелей", variable=var_sixpanel).place(x=300, y=80)
tk.Checkbutton(root, text="Цикличные видео", variable=var_loop).place(x=400, y=80)
tk.Checkbutton(root, text="Открыть папку после", variable=open_folder_after).place(x=520, y=80)

start_button.place(x=20, y=120)
output_text.place(x=20, y=160)
progress_bar.place(x=20, y=560)

root.mainloop()
