import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageTk
import threading

class GitHubUserFinder:
    def __init__(self, window):
        self.window = window
        self.window.title("GitHub User Finder")
        self.window.geometry("1000x700")
        
        # API настройки
        self.api_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Файл для сохранения избранных
        self.favorites_file = "favorites.json"
        self.favorites = []
        self.load_favorites()
        
        # Текущие результаты поиска
        self.search_results = []
        
        # Создание GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка сетки
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Секция поиска
        search_frame = ttk.LabelFrame(main_frame, text="Поиск пользователя GitHub", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Введите имя пользователя:").grid(row=0, column=0, padx=(0, 5))
        
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, padx=(0, 5))
        self.search_entry.bind('<Return>', lambda event: self.search_user())
        
        ttk.Button(search_frame, text="Поиск", command=self.search_user).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(search_frame, text="Очистить", command=self.clear_search).grid(row=0, column=3)
        
        # Панель с результатами
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Секция результатов поиска
        results_frame = ttk.LabelFrame(content_frame, text="Результаты поиска", padding="10")
        results_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Дерево результатов
        columns = ("username", "name", "repos", "followers")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        self.results_tree.heading("username", text="Username")
        self.results_tree.heading("name", text="Имя")
        self.results_tree.heading("repos", text="Репозитории")
        self.results_tree.heading("followers", text="Подписчики")
        
        self.results_tree.column("username", width=150)
        self.results_tree.column("name", width=200)
        self.results_tree.column("repos", width=100)
        self.results_tree.column("followers", width=100)
        
        self.results_tree.bind('<Double-1>', self.show_user_details)
        
        # Скроллбар для результатов
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка добавления в избранное
        ttk.Button(results_frame, text="Добавить в избранное", 
                  command=self.add_to_favorites).pack(pady=(10, 0))
        
        # Секция избранного
        favorites_frame = ttk.LabelFrame(content_frame, text="Избранные пользователи", padding="10")
        favorites_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.favorites_listbox = tk.Listbox(favorites_frame, height=15)
        favorites_scrollbar = ttk.Scrollbar(favorites_frame, orient=tk.VERTICAL, command=self.favorites_listbox.yview)
        self.favorites_listbox.configure(yscrollcommand=favorites_scrollbar.set)
        
        self.favorites_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        favorites_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.favorites_listbox.bind('<Double-1>', self.show_favorite_details)
        
        # Кнопки управления избранным
        fav_buttons_frame = ttk.Frame(favorites_frame)
        fav_buttons_frame.pack(pady=(10, 0))
        
        ttk.Button(fav_buttons_frame, text="Показать детали", 
                  command=self.show_selected_favorite).pack(pady=(0, 5))
        ttk.Button(fav_buttons_frame, text="Удалить из избранного", 
                  command=self.remove_from_favorites).pack()
        
        # Секция детальной информации
        self.details_frame = ttk.LabelFrame(main_frame, text="Детальная информация", padding="10")
        self.details_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Аватар
        self.avatar_label = ttk.Label(self.details_frame)
        self.avatar_label.grid(row=0, column=0, rowspan=5, padx=(0, 20))
        
        # Информация о пользователе
        self.name_label = ttk.Label(self.details_frame, text="Имя: ", font=('Arial', 10, 'bold'))
        self.name_label.grid(row=0, column=1, sticky=tk.W)
        
        self.bio_label = ttk.Label(self.details_frame, text="Био: ", wraplength=600)
        self.bio_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        self.location_label = ttk.Label(self.details_frame, text="Локация: ")
        self.location_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        self.company_label = ttk.Label(self.details_frame, text="Компания: ")
        self.company_label.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        self.stats_label = ttk.Label(self.details_frame, text="")
        self.stats_label.grid(row=4, column=1, sticky=tk.W, pady=(5, 0))
        
        # Загрузка избранных
        self.refresh_favorites()
        
    def search_user(self):
        """Поиск пользователя GitHub"""
        query = self.search_entry.get().strip()
        
        if not query:
            messagebox.showerror("Ошибка", "Поле поиска не может быть пустым!")
            return
        
        # Показываем индикатор загрузки
        self.window.config(cursor="watch")
        self.window.update()
        
        # Запускаем поиск в отдельном потоке
        thread = threading.Thread(target=self._perform_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _perform_search(self, query):
        """Выполнение поиска в отдельном потоке"""
        try:
            # Поиск пользователей
            response = requests.get(
                f"{self.api_url}/search/users",
                headers=self.headers,
                params={"q": query, "per_page": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.search_results = data.get("items", [])
                
                # Обновляем GUI в главном потоке
                self.window.after(0, self._update_search_results)
            elif response.status_code == 403:
                self.window.after(0, lambda: messagebox.showerror(
                    "Ошибка API", 
                    "Достигнут лимит запросов к API GitHub. Пожалуйста, подождите несколько минут."
                ))
            else:
                self.window.after(0, lambda: messagebox.showerror(
                    "Ошибка", 
                    f"Ошибка при поиске: {response.status_code}"
                ))
        
        except requests.exceptions.RequestException as e:
            self.window.after(0, lambda: messagebox.showerror(
                "Ошибка сети", 
                f"Не удалось выполнить запрос: {str(e)}"
            ))
        
        finally:
            self.window.after(0, lambda: self.window.config(cursor=""))
    
    def _update_search_results(self):
        """Обновление результатов поиска в GUI"""
        # Очистка дерева
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Заполнение результатами
        for user in self.search_results:
            self.results_tree.insert("", tk.END, values=(
                user["login"],
                user.get("name", "Н/Д"),
                user.get("public_repos", "Н/Д"),
                user.get("followers", "Н/Д")
            ))
    
    def show_user_details(self, event=None):
        """Показать детальную информацию о выбранном пользователе"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для просмотра деталей")
            return
        
        username = self.results_tree.item(selection[0])["values"][0]
        self._load_user_details(username)
    
    def show_selected_favorite(self):
        """Показать детали выбранного избранного пользователя"""
        selection = self.favorites_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из избранного")
            return
        
        username = self.favorites[selection[0]]
        self._load_user_details(username)
    
    def show_favorite_details(self, event=None):
        """Обработчик двойного клика по избранному"""
        self.show_selected_favorite()
    
    def _load_user_details(self, username):
        """Загрузка детальной информации о пользователе"""
        thread = threading.Thread(target=self._fetch_user_details, args=(username,))
        thread.daemon = True
        thread.start()
    
    def _fetch_user_details(self, username):
        """Получение детальной информации в отдельном потоке"""
        try:
            response = requests.get(
                f"{self.api_url}/users/{username}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Загрузка аватара
                avatar_url = user_data.get("avatar_url")
                if avatar_url:
                    avatar_response = requests.get(avatar_url)
                    if avatar_response.status_code == 200:
                        image_data = BytesIO(avatar_response.content)
                        image = Image.open(image_data)
                        image = image.resize((100, 100), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        # Сохраняем ссылку на фото
                        self.current_photo = photo
                        
                        # Обновляем GUI
                        self.window.after(0, lambda: self._update_user_details(user_data, photo))
                    else:
                        self.window.after(0, lambda: self._update_user_details(user_data, None))
                else:
                    self.window.after(0, lambda: self._update_user_details(user_data, None))
            else:
                self.window.after(0, lambda: messagebox.showerror(
                    "Ошибка", f"Не удалось загрузить данные пользователя: {response.status_code}"
                ))
        
        except requests.exceptions.RequestException as e:
            self.window.after(0, lambda: messagebox.showerror(
                "Ошибка сети", f"Не удалось загрузить данные: {str(e)}"
            ))
    
    def _update_user_details(self, user_data, photo):
        """Обновление GUI с детальной информацией"""
        # Обновление аватара
        if photo:
            self.avatar_label.configure(image=photo)
        else:
            self.avatar_label.configure(image="")
        
        # Обновление информации
        self.name_label.configure(text=f"Имя: {user_data.get('name', 'Не указано')}")
        
        bio = user_data.get("bio")
        self.bio_label.configure(text=f"Био: {bio if bio else 'Не указано'}")
        
        location = user_data.get("location")
        self.location_label.configure(text=f"Локация: {location if location else 'Не указана'}")
        
        company = user_data.get("company")
        self.company_label.configure(text=f"Компания: {company if company else 'Не указана'}")
        
        stats = (
            f"Публичные репозитории: {user_data.get('public_repos', 0)} | "
            f"Подписчики: {user_data.get('followers', 0)} | "
            f"Подписки: {user_data.get('following', 0)}"
        )
        self.stats_label.configure(text=stats)
    
    def add_to_favorites(self):
        """Добавление пользователя в избранное"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для добавления в избранное")
            return
        
        username = self.results_tree.item(selection[0])["values"][0]
        
        if username in self.favorites:
            messagebox.showinfo("Информация", f"Пользователь {username} уже в избранном")
            return
        
        self.favorites.append(username)
        self.save_favorites()
        self.refresh_favorites()
        messagebox.showinfo("Успех", f"Пользователь {username} добавлен в избранное")
    
    def remove_from_favorites(self):
        """Удаление пользователя из избранного"""
        selection = self.favorites_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления из избранного")
            return
        
        username = self.favorites[selection[0]]
        
        if messagebox.askyesno("Подтверждение", f"Удалить {username} из избранного?"):
            self.favorites.remove(username)
            self.save_favorites()
            self.refresh_favorites()
            messagebox.showinfo("Успех", f"Пользователь {username} удален из избранного")
    
    def refresh_favorites(self):
        """Обновление списка избранного"""
        self.favorites_listbox.delete(0, tk.END)
        for user in self.favorites:
            self.favorites_listbox.insert(tk.END, user)
    
    def clear_search(self):
        """Очистка поиска"""
        self.search_entry.delete(0, tk.END)
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.search_results = []
    
    def save_favorites(self):
        """Сохранение избранных в JSON"""
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump({
                    "favorites": self.favorites,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {str(e)}")
    
    def load_favorites(self):
        """Загрузка избранных из JSON"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorites = data.get("favorites", [])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить избранное: {str(e)}")
                self.favorites = []

if __name__ == "__main__":
    window = tk.Tk()
    app = GitHubUserFinder(window)
    window.mainloop()
