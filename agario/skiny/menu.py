from customtkinter import *
from tkinter import ttk


class ConnectWindow(CTk):
    def __init__(self):
        super().__init__()

        self.name = None
        self.host = None
        self.port = None
        self.selected_skin = 'default'  # Додано вибір скіна

        self.title('Agario Launcher')
        self.geometry('400x550')  # Збільшено висоту для селектора скіна

        # Заголовок
        CTkLabel(self, text='🎮 Agario Game Launcher',
                 font=('Arial', 24, 'bold')).pack(pady=20)

        # Секція підключення
        connection_frame = CTkFrame(self)
        connection_frame.pack(pady=10, padx=20, fill='x')

        CTkLabel(connection_frame, text='Підключення до сервера:',
                 font=('Arial', 16, 'bold')).pack(pady=10)

        self.name_entry = CTkEntry(connection_frame, placeholder_text='Введіть ім\'я гравця',
                                   height=40, font=('Arial', 12))
        self.name_entry.pack(padx=20, pady=5, fill='x')

        self.host_entry = CTkEntry(connection_frame, placeholder_text='IP адреса (localhost)',
                                   height=40, font=('Arial', 12))
        self.host_entry.pack(padx=20, pady=5, fill='x')
        self.host_entry.insert(0, 'localhost')  # Значення за замовчуванням

        self.port_entry = CTkEntry(connection_frame, placeholder_text='Порт (8080)',
                                   height=40, font=('Arial', 12))
        self.port_entry.pack(padx=20, pady=5, fill='x')
        self.port_entry.insert(0, '8080')  # Значення за замовчуванням

        # Секція вибору скіна
        skin_frame = CTkFrame(self)
        skin_frame.pack(pady=10, padx=20, fill='x')

        CTkLabel(skin_frame, text='🎨 Виберіть скін:',
                 font=('Arial', 16, 'bold')).pack(pady=10)

        # Список доступних скінів з описами
        self.skins_info = {
            'default': '🟢 Стандартний (зелений)',
            'football': '⚽ Футбольний м\'яч',
            'earth': '🌍 Планета Земля',
            'mars': '🔴 Планета Марс',
            'sun': '☀️ Сонце',
            'moon': '🌙 Місяць',
            'fire': '🔥 Вогонь (анімований)',
            'water': '💧 Вода (анімована)',
            'toxic': '☢️ Токсичний (анімований)',
            'rainbow': '🌈 Райдуга (анімована)',
            'galaxy': '🌌 Галактика (зі зірками)',
            'lava': '🌋 Лава (анімована)'
        }

        # Комбобокс для вибору скіна
        self.skin_var = StringVar(value='default')
        self.skin_combo = CTkComboBox(skin_frame,
                                      values=list(self.skins_info.keys()),
                                      command=self.on_skin_change,
                                      height=40, font=('Arial', 12))
        self.skin_combo.pack(padx=20, pady=5, fill='x')
        self.skin_combo.set('default')

        # Опис вибраного скіна
        self.skin_description = CTkLabel(skin_frame,
                                         text=self.skins_info['default'],
                                         font=('Arial', 12))
        self.skin_description.pack(pady=5)

        # Попередній перегляд скіна (текстовий)
        preview_frame = CTkFrame(skin_frame)
        preview_frame.pack(pady=10, padx=20, fill='x')

        CTkLabel(preview_frame, text='Попередній перегляд:',
                 font=('Arial', 12, 'bold')).pack(pady=5)

        self.skin_preview = CTkLabel(preview_frame,
                                     text=self.get_skin_preview('default'),
                                     font=('Arial', 20))
        self.skin_preview.pack(pady=5)

        # Інструкції
        instructions_frame = CTkFrame(self)
        instructions_frame.pack(pady=10, padx=20, fill='x')

        CTkLabel(instructions_frame, text='📋 Керування в грі:',
                 font=('Arial', 14, 'bold')).pack(pady=5)

        instructions_text = """
• WASD - рух
• 1-9 - зміна скіна в грі
• TAB - показати/сховати меню скінів
• Мета: поглинати інших гравців та їжу
        """

        CTkLabel(instructions_frame, text=instructions_text.strip(),
                 font=('Arial', 11), justify='left').pack(pady=5)

        # Кнопка підключення
        self.connect_button = CTkButton(self, text='🚀 Приєднатися до гри',
                                        command=self.open_game,
                                        height=50, font=('Arial', 16, 'bold'),
                                        fg_color='#2196F3', hover_color='#1976D2')
        self.connect_button.pack(pady=20, padx=20, fill='x')

        # Статус
        self.status_label = CTkLabel(self, text='Готовий до підключення',
                                     font=('Arial', 10))
        self.status_label.pack(pady=5)

    def get_skin_preview(self, skin_name):
        """Повертає текстовий попередній перегляд скіна"""
        previews = {
            'default': '●',
            'football': '⚽',
            'earth': '🌍',
            'mars': '🔴',
            'sun': '☀️',
            'moon': '🌙',
            'fire': '🔥',
            'water': '💧',
            'toxic': '☢️',
            'rainbow': '🌈',
            'galaxy': '🌌',
            'lava': '🌋'
        }
        return previews.get(skin_name, '●')

    def on_skin_change(self, selected_skin):
        """Обробник зміни скіна"""
        self.selected_skin = selected_skin
        self.skin_description.configure(text=self.skins_info[selected_skin])
        self.skin_preview.configure(text=self.get_skin_preview(selected_skin))

    def validate_input(self):
        """Перевіряє коректність введених даних"""
        if not self.name_entry.get().strip():
            self.status_label.configure(text='❌ Введіть ім\'я гравця!', text_color='red')
            return False

        if not self.host_entry.get().strip():
            self.status_label.configure(text='❌ Введіть IP адресу!', text_color='red')
            return False

        try:
            port = int(self.port_entry.get())
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            self.status_label.configure(text='❌ Введіть коректний порт (1-65535)!', text_color='red')
            return False

        if len(self.name_entry.get().strip()) > 20:
            self.status_label.configure(text='❌ Ім\'я занадто довге (макс. 20 символів)!', text_color='red')
            return False

        return True

    def open_game(self):
        """Відкриває гру після валідації"""
        if not self.validate_input():
            return

        self.status_label.configure(text='✅ Підключення...', text_color='green')
        self.connect_button.configure(state='disabled', text='Підключення...')

        # Оновлюємо інтерфейс
        self.update()

        try:
            self.name = self.name_entry.get().strip()
            self.host = self.host_entry.get().strip()
            self.port = int(self.port_entry.get())
            self.selected_skin = self.skin_combo.get()

            # Закриваємо вікно
            self.destroy()

        except Exception as e:
            self.status_label.configure(text=f'❌ Помилка: {str(e)}', text_color='red')
            self.connect_button.configure(state='normal', text='🚀 Приєднатися до гри')