import numpy as np
import imageio.v2 as imageio
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import sdtfile
import os


def turn_sdt(file_path):
    return sdtfile.SdtFile(file_path)


def normalize_frame(frame, scale_factor):
    frame -= np.min(frame)
    frame *= scale_factor
    frame /= np.max(frame) if np.max(frame) > 0 else 1
    return (frame * 255).astype(np.uint8)


def create_color_frame(gray_frame, color):
    rgb = np.zeros((gray_frame.shape[0], gray_frame.shape[1], 3), dtype=np.uint8)
    if color == "red":
        rgb[:, :, 0] = gray_frame
    elif color == "green":
        rgb[:, :, 1] = gray_frame
    return rgb


def draw_text(image_np, text):
    image = Image.fromarray(image_np)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), text, fill=(255, 255, 255), font=font)
    return np.array(image)


def process_frames(sdt, k, channels, fps, accumulate=False, suffix="", filename_label="", progress_callback=None, output_dir="frames"):
    os.makedirs(output_dir, exist_ok=True)

    valid_indices = list(range(205, 370)) + list(range(370, 980))
    total_frames = len(valid_indices)
    accumulation_buffers = {ch: np.zeros((512, 512), dtype=np.float32) for ch in channels}
    accumulation_count = {ch: 0 for ch in channels}

    writers = {
        ch: imageio.get_writer(os.path.join(output_dir, f'channel_{ch}{suffix}.mp4'), fps=fps) for ch in channels
    }
    combined_writer = imageio.get_writer(os.path.join(output_dir, f'combined_video{suffix}.mp4'), fps=fps)

    for i, frame_idx in enumerate(valid_indices):
        frames = {}
        combined = np.zeros((512, 512, 3), dtype=np.uint8)

        for ch, color in channels.items():
            raw = np.array(sdt.data[ch][:, :, frame_idx], dtype=np.float32)
            if accumulate:
                accumulation_buffers[ch] += raw
                accumulation_count[ch] += 1
                raw = accumulation_buffers[ch] / accumulation_count[ch]
                gray = normalize_frame(raw, 1)
            else:
                gray = normalize_frame(raw, k[ch])

            color_frame = create_color_frame(gray, color)
            color_frame = draw_text(color_frame, filename_label)
            writers[ch].append_data(color_frame)
            frames[ch] = color_frame

        if 0 in frames and 2 in frames:
            combined = np.clip(frames[0].astype(np.int16) + frames[2].astype(np.int16), 0, 255).astype(np.uint8)
        elif 0 in frames:
            combined = frames[0]
        elif 2 in frames:
            combined = frames[2]

        combined = draw_text(combined, filename_label)
        combined_writer.append_data(combined)

        if progress_callback:
            progress_callback((i + 1) / total_frames * 100)

    for writer in writers.values():
        writer.close()
    combined_writer.close()

    print(f"Видео с суффиксом '{suffix}' сохранено в папке {output_dir}.")


def stack_horizontally(imgs):
    return np.hstack(imgs)


def stack_vertically(imgs):
    return np.vstack(imgs)


def create_six_panel_video(frame_size, fps, output_dir, progress_callback=None):
    filenames = [
        'channel_0_обычное.mp4',
        'channel_2_обычное.mp4',
        'combined_video_обычное.mp4',
        'channel_0_необычное.mp4',
        'channel_2_необычное.mp4',
        'combined_video_необычное.mp4'
    ]
    filepaths = [os.path.join(output_dir, f) for f in filenames]

    readers = [imageio.get_reader(f) for f in filepaths]
    num_frames = min([reader.count_frames() for reader in readers])
    writer = imageio.get_writer(os.path.join(output_dir, 'six_panel_video.mp4'), fps=fps)

    for i in range(num_frames):
        frames = [reader.get_data(i) for reader in readers]
        top_row = stack_horizontally(frames[:3])
        bottom_row = stack_horizontally(frames[3:])
        panel = stack_vertically([top_row, bottom_row])
        writer.append_data(panel)

        if progress_callback:
            progress_callback((i + 1) / num_frames * 100)

    for reader in readers:
        reader.close()
    writer.close()
    print(f"Финальное видео сохранено в {os.path.join(output_dir, 'six_panel_video.mp4')}")
