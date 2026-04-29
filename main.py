import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import os
from io import BytesIO
from PIL import Image, ImageTk  # для отображения аватаров (можно не использовать, если изображения не нужны)

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")

        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()

        # --- Поисковая строка ---
        search_frame = tk.Frame(root)
        search_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(search_frame, text="Введите имя пользователя:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_button = tk.Button(search_frame, text="Поиск", command=self.search_users)
        self.search_button.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.search_users())

        # --- Результаты поиска ---
        results_frame = tk.LabelFrame(root, text="Результаты поиска", padx=5, pady=5)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview для табличного отображения
        columns = ("login", "avatar", "url")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="browse")
        self.results_tree.heading("login", text="Логин")
        self.results_tree.heading("avatar", text="Аватар")
        self.results_tree.heading("url", text="Профиль")
        self.results_tree.column("login", width=200)
        self.results_tree.column("avatar", width=100)
        self.results_tree.column("url", width=300)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        # Кнопки действий с результатом
        action_frame = tk.Frame(root)
        action_frame.pack(pady=5)
        self.add_fav_button = tk.Button(action_frame, text="Добавить в избранное", command=self.add_to_favorites, state=tk.DISABLED)
        self.add_fav_button.pack(side=tk.LEFT, padx=5)
        self.show_details_button = tk.Button(action_frame, text="Показать детали", command=self.show_user_details, state=tk.DISABLED)
        self.show_details_button.pack(side=tk.LEFT, padx=5)

        # Привязка события выбора строки
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        # --- Избранное ---
        fav_frame = tk.LabelFrame(root, text="Избранные пользователи", padx=5, pady=5)
        fav_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.fav_listbox = tk.Listbox(fav_frame, height=8)
        self.fav_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar = ttk.Scrollbar(fav_frame, orient=tk.VERTICAL, command=self.fav_listbox.yview)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.fav_listbox.configure(yscrollcommand=fav_scrollbar.set)

        remove_fav_button = tk.Button(root, text="Удалить из избранного", command=self.remove_from_favorites)
        remove_fav_button.pack(pady=5)

        # Заполняем избранное при старте
        self.refresh_favorites_listbox()

    # ---------- Загрузка/сохранение избранного ----------
    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_favorites(self):
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=4)

    def refresh_favorites_listbox(self):
        self.fav_listbox.delete(0, tk.END)
        for user in self.favorites:
            self.fav_listbox.insert(tk.END, user["login"])

    # ---------- Поиск пользователей через GitHub API ----------
    def search_users(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Проверка ввода", "Поле поиска не должно быть пустым.")
            return

        # Очищаем предыдущие результаты
        for row in self.results_tree.get_children():
            self.results_tree.delete(row)

        url = f"https://api.github.com/search/users?q={query}"
        try:
            response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
            if response.status_code == 200:
                data = response.json()
                users = data.get("items", [])
                if not users:
                    messagebox.showinfo("Результат", "Пользователи не найдены.")
                    return

                # Вставляем результаты в Treeview (отображаем логин, аватар позже)
                for user in users:
                    # Для упрощения не будем сразу загружать аватары, чтобы не замедлять интерфейс.
                    # Можно добавить колонку с мини-картинкой при помощи PIL, но оставим базово.
                    self.results_tree.insert("", tk.END, values=(user["login"], user["avatar_url"], user["html_url"]))
            else:
                messagebox.showerror("Ошибка API", f"HTTP {response.status_code}: {response.json().get('message', '')}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить запрос: {e}")

    # ---------- Взаимодействие с результатами ----------
    def on_result_select(self, event):
        selected = self.results_tree.selection()
        if selected:
            self.add_fav_button.config(state=tk.NORMAL)
            self.show_details_button.config(state=tk.NORMAL)
        else:
            self.add_fav_button.config(state=tk.DISABLED)
            self.show_details_button.config(state=tk.DISABLED)

    def get_selected_user_info(self):
        selected = self.results_tree.selection()
        if not selected:
            return None
        item = self.results_tree.item(selected[0])
        values = item["values"]
        return {
            "login": values[0],
            "avatar_url": values[1],
            "html_url": values[2]
        }

    def add_to_favorites(self):
        user_info = self.get_selected_user_info()
        if not user_info:
            return
        # Проверяем, не добавлен ли уже
        if any(u["login"] == user_info["login"] for u in self.favorites):
            messagebox.showinfo("Информация", f"Пользователь {user_info['login']} уже в избранном.")
            return
        self.favorites.append(user_info)
        self.save_favorites()
        self.refresh_favorites_listbox()
        messagebox.showinfo("Избранное", f"{user_info['login']} добавлен в избранное.")

    def show_user_details(self):
        user_info = self.get_selected_user_info()
        if not user_info:
            return
        # Получаем более подробную информацию через дополнительный запрос
        url = f"https://api.github.com/users/{user_info['login']}"
        try:
            response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
            if response.status_code == 200:
                details = response.json()
                info = (
                    f"Логин: {details.get('login')}\n"
                    f"Имя: {details.get('name') or 'не указано'}\n"
                    f"Компания: {details.get('company') or 'не указана'}\n"
                    f"Блог: {details.get('blog') or 'нет'}\n"
                    f"Локация: {details.get('location') or 'не указана'}\n"
                    f"Публичные репозитории: {details.get('public_repos')}\n"
                    f"Подписчики: {details.get('followers')}\n"
                    f"Подписки: {details.get('following')}\n"
                    f"Профиль: {details.get('html_url')}"
                )
                messagebox.showinfo(f"Детали: {user_info['login']}", info)
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить детали: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def remove_from_favorites(self):
        selected_indices = self.fav_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Предупреждение", "Выберите пользователя в списке избранных.")
            return
        index = selected_indices[0]
        login = self.fav_listbox.get(index)
        self.favorites = [u for u in self.favorites if u["login"] != login]
        self.save_favorites()
        self.refresh_favorites_listbox()
        messagebox.showinfo("Избранное", f"{login} удалён из избранного.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
