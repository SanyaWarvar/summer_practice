import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter as tk
from PIL import Image, ImageEnhance, ImageTk
import cv2
from threading import Thread
import time


class App(ctk.CTk):
    def __init__(self):
        """Инициализация приложения

        Создаются основные окна для работы с программой
        """
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")
        self.tk_im = None
        self.image_on_canvas = None
        self.working_img = None
        self.img_cv2 = None

        check_data_thread = Thread(target=self.check_data)

        self.title("ToadsTools Graphics")
        self.geometry("1100x600")
        self.iconbitmap("toad.ico")

        toolbar = ctk.CTkFrame(master=self)
        toolbar.pack(anchor="nw")

        self.user_image = tk.Canvas(master=self, bg="#242424", highlightbackground="#242424")
        self.user_image.pack(side="top", fill="both", expand=True)

        self.curX = None
        self.curY = None
        self.start_x = None
        self.start_y = None

        self.current_image = ctk.CTkLabel(master=self.user_image, text="")
        self.current_image.pack()

        open_directory = ctk.CTkButton(
            master=toolbar, text="Открыть изображение",
            command=lambda: self.open_f()
        )
        open_directory.pack(side="left")

        size = ctk.CTkFrame(master=toolbar)
        size.pack(side="left")

        self.width_entry = ctk.CTkEntry(master=size, placeholder_text="Ширина")
        self.height_entry = ctk.CTkEntry(master=size, placeholder_text="Высота")
        self.angle_entry = ctk.CTkEntry(master=size, placeholder_text="Угол наклона")
        self.sharpness_entry = ctk.CTkEntry(master=size, placeholder_text="Резкость")

        self.width_entry.pack(side="top")
        self.height_entry.pack(side="top")
        self.angle_entry.pack(side="top")
        self.sharpness_entry.pack(side="top")

        ctk.CTkButton(
            master=size, text="Подтвердить",
            command=lambda: self.view_image(image=self.working_img)
        ).pack(side="bottom")

        self.crn_img = None

        color_mode_frame = ctk.CTkFrame(master=toolbar)
        color_mode_frame.pack(side="left")
        self.mode = "standard"

        mode_color = {"Обычный": "gray", "Красный": "red", "Зеленый": "green", "Синий": "blue"}
        self.radio_var = tk.StringVar()
        for k, v in mode_color.items():
            b = ctk.CTkRadioButton(
                master=color_mode_frame, fg_color=v, text=k, value=v, hover_color=v,
                variable=self.radio_var
            )
            b.pack(side="top")
            if k == "Обычный":
                b.select()

        draw_frame = ctk.CTkFrame(master=toolbar)
        draw_frame.pack(side="left")
        draw_coord_frame = ctk.CTkFrame(master=draw_frame)
        draw_coord_frame.pack(side="left")

        self.thickness_entry = ctk.CTkEntry(master=draw_frame, placeholder_text="Толщина линии")

        self.coord = []
        for i in ("X начальное", "Y начальное", "X конечное", "Y конечное"):
            self.coord.append(ctk.CTkEntry(master=draw_coord_frame, placeholder_text=i))
            self.coord[-1].pack(side="top")
        ctk.CTkButton(
            master=draw_coord_frame, text="Создать линию", command=lambda:
            self.draw((self.coord[0].get(), self.coord[1].get()), (self.coord[2].get(), self.coord[3].get()))
        ).pack(side="top")

        self.thickness_entry.pack()
        check_data_thread.start()

    def open_f(self, path=None):
        """Открытие файла

        Открывается изображение (png, jpg), используя полученный путь. Если путь некорректен или не существует,
        то пользователь выбирает файл сам при помощи проводника.
        :param path: путь до изображения (png, jpg).
        :type path: str
        """
        f_types = [('Png Files', '*.png'), ('Jpg Files', '*.jpg')]
        if not path or not path.endswith((".png", ".jpg")):
            path = fd.askopenfilename(title="Открыть папку", initialdir="/", filetypes=f_types)

        self.img_cv2 = cv2.imread(path)

        self.img_cv2 = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2RGB)
        self.working_img = self.img_cv2.copy()

        self.view_image(self.working_img)

    def view_image(self, image):
        """Отображение изображения в приложении

        В приложении отображается выбранное ранее изображение.
        Над изображением выполняется все необходимые махинации
        (изменение размеры, резкости, поворот, отображение выбранного цветового канала).
        :param image: Изображение, которое должно отображаться в приложении.
        :type image: numpy.ndarray
        """
        if image is None:
            return

        angle = self.angle_entry.get()
        if angle == "":
            angle = 0

        if self.type_test(float, angle):
            angle = float(angle)
        else:
            return

        if self.width_entry.get() == "":
            width = self.img_cv2.shape[1]
        else:
            width = int(self.width_entry.get())

        if self.height_entry.get() == "":
            height = self.img_cv2.shape[0]
        else:
            height = int(self.height_entry.get())

        size = (width, height)

        if self.sharpness_entry.get() == "":
            sharp = 0
        else:
            sharp = float(self.sharpness_entry.get())

        image = self.change_color(self.radio_var.get(), image)

        image = ImageEnhance.Sharpness(Image.fromarray(image).rotate(angle, expand=True)).enhance(sharp)

        self.working_img = cv2.resize(self.working_img, dsize=size)
        image = image.resize(size)

        self.tk_im = ImageTk.PhotoImage(image)
        if self.image_on_canvas:
            self.user_image.itemconfig(self.image_on_canvas, image=self.tk_im)
            self.user_image.configure(width=size[0], height=size[1])
        else:
            self.image_on_canvas = self.user_image.create_image(0, 0, anchor="nw", image=self.tk_im)

        self.user_image.bind("<ButtonPress-1>", self.on_button_press)
        self.user_image.bind("<B1-Motion>", self.on_move_press)

    @staticmethod
    def change_color(mode, image):
        """Изменение цветового канала

        Изменяется цветовой канал (обычный, красный, синий, зеленый) выбранного изображения.
        :param mode: Выбранный цветовой канал.
        :type mode: str
        :param image: Изображение, цветовой канал которого будет изменяться.
        :type image: numpy.ndarray
        :return: Изображение с измененным цветовым каналом
        """

        new_img = image.copy()

        if mode == "blue":
            new_img[:, :, 0] = 0
            new_img[:, :, 1] = 0
        elif mode == "red":
            new_img[:, :, 1] = 0
            new_img[:, :, 2] = 0
        elif mode == "green":
            new_img[:, :, 0] = 0
            new_img[:, :, 2] = 0

        return new_img

    def check_data(self):
        """Проверка валидности данных в окнах ввода.

        Функция запускается вторым потоком, и каждые 0.2 секунды проверяет валидность в каждом из окон для ввода.
        В случае невалидности обводка окна становится красной, иначе остается серой.
        """
        d = {
            self.thickness_entry: int,
            self.height_entry: int,
            self.width_entry: int,
            self.angle_entry: float,
            self.sharpness_entry: float,
            self.coord[0]: int,
            self.coord[1]: int,
            self.coord[2]: int,
            self.coord[3]: int

        }
        while True:
            time.sleep(0.2)
            for k, v in d.items():
                if k.get() != "" and not (self.type_test(v, k.get())):
                    k.configure(border_color="red")
                    k.pack()
                else:
                    k.configure(border_color="#909090")
                    k.pack()

    def on_button_press(self, event):
        """Нажатие лкм

        Запускается при нажатии лкм в области изображения. Сохраняет координаты курсора и запускает функцию
        рисования линии по координатам курсора.
        :param event: Хранит координаты (x, y) курсора в данным момент времени.
        :type event: tkinter.Event
        """

        self.start_x, self.start_y = event.x, event.y
        self.curX, self.curY = self.start_x, self.start_y
        if self.angle_entry.get() in ("", "0"):
            self.draw((self.start_x, self.start_y), (self.curX, self.curY))

    def on_move_press(self, event):
        """Удержание лкм

        Запускается при удержании лкм в области изображения. Сохраняет координаты курсора и запускает функцию
        рисования линии по координатам курсора.
        :param event: Хранит координаты (x, y) курсора в данным момент времени.
        :type event: tkinter.Event
        """
        if self.working_img is None:
            return

        self.curX, self.curY = event.x, event.y
        if self.angle_entry.get() in ("", "0"):
            self.draw((self.start_x, self.start_y), (self.curX, self.curY))
        self.start_x = event.x
        self.start_y = event.y

    def draw(self, start_coord, end_coord):
        """Создании зеленой линии

        На изображении создается зеленая линия выбранной толщины по выбранным координатам.
        Если изображение не выбрано, то функция прерывается.
        :param start_coord: Начальные координаты.
        :type start_coord: tuple(int, int), tuple(str, str)
        :param end_coord: Конечные координаты.
        :type end_coord: tuple(int, int), tuple(str, str)
        """
        if self.working_img is None:
            return
        for cur in (*start_coord, *end_coord):
            if not self.type_test(int, cur):
                return

        thickness = self.thickness_entry.get()
        if thickness == "":
            thickness = 1
        elif not self.type_test(int, thickness):
            return
        else:
            thickness = int(thickness)

        start_x, start_y = list(map(int, start_coord))
        end_x, end_y = list(map(int, end_coord))
        cv2.line(self.working_img, (start_x, start_y), (end_x, end_y), (0, 255, 0), thickness=thickness)
        self.view_image(self.working_img)

    @staticmethod
    def type_test(to_type, verifiable):
        """Проверка на тип

        Проверка на то можно ли преобразовать объект в нужный тип. Например, можно ли преобразовать строку в число.
        :param to_type: Класс в которым мы хотим преобразовать объект. Например, int.
        :type to_type: any class
        :param verifiable: Объект, который мы проверяем на возможность преобразования.
        :type verifiable: any
        :return: True, если объект можно преобразовать, иначе False.
        """
        if to_type not in [int, float]:
            return False

        try:
            to_type(verifiable)
            return True
        except ValueError:
            return False


if __name__ == '__main__':
    app = App()
    app.mainloop()
