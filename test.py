import sdtfile
import os


def check_sdt_file(file_path):
    """Проверяет SDT файл и ищет frame time или временные метки для кадров."""
    if not os.path.exists(file_path):
        print("Ошибка: Файл не найден.")
        return

    try:
        # Загружаем SDT файл
        sdt = sdtfile.SdtFile(file_path)
        print(f"Файл {file_path} успешно загружен.")

        # Пытаемся найти временные метки для каждого кадра
        frame_time = None

        frame_time = sdt.times


        if frame_time:

            print(f"\nНайдено {len(frame_time)} временных меток (frame time):")
            for idx, time in enumerate(frame_time):
                print(f"Кадр {idx + 1}: время {time} секунд")
        else:
            print("В SDT файле не найдены временные метки для кадров.")
        print(frame_time[0])
        print(frame_time[2])
        print(frame_time[0]-frame_time[2])
    except Exception as e:
        print(f"Ошибка при чтении SDT файла: {e}")


# Путь к SDT файлу
file_path = "9.sdt"  # Укажите путь к вашему SDT файлу
check_sdt_file(file_path)


