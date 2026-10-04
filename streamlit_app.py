import streamlit as st
import requests
import time
import pandas as pd

# Ссылка на вашу базу Firebase
PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products.json"

# НАСТРОЙКА ПАРОЛЕЙ ДЛЯ РАЗДЕЛЕНИЯ ДОСТУПА (Можно заменить на свои)
PASSWORD_STAFF = "4444"  # Пароль для Старшего продавца (только добавление)
PASSWORD_ADMIN = "1608"  # Пароль для Вас / Директора (полный контроль и редактирование)

st.set_page_config(page_title="База Артикулов", page_icon="📦", layout="centered")
st.title("📦 Умная База Артикулов")

def load_data():
    try:
        response = requests.get(FIREBASE_URL, timeout=3)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

products_db = load_data()

# Собираем список групп, которые реально существуют в базе
detected_groups = set()
if products_db:
    for data in products_db.values():
        if isinstance(data, dict):
            detected_groups.add(data.get("group", "Без группы"))
        else:
            detected_groups.add("Без группы")

if not detected_groups:
    detected_groups = {"Конфлены", "Печенье", "Чай/Кофе", "Разное"}

existing_groups = sorted(list(detected_groups - {"Без группы"}))
if not existing_groups:
    existing_groups = ["Конфеты", "Печенье", "Чай/Кофе", "Разное"]

all_groups = sorted(list(detected_groups | {"Без группы"}))
grouped_products = {g: {} for g in all_groups}

if products_db:
    for name, data in products_db.items():
        g = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
        art = data.get("article", data) if isinstance(data, dict) else data
        if g not in grouped_products:
            grouped_products[g] = {}
        grouped_products[g][name] = art

# 1. БЛОК ПОИСКА И ОТОБРАЖЕНИЯ ДЛЯ ПРОДАВЦОВ
st.subheader("🔍 Поиск и Просмотр")
search_query = st.text_input("Введите или наговорите название товара для быстрого поиска:")

if search_query:
    filtered = {k: v for k, v in products_db.items() if search_query.lower() in k.lower()}
    if filtered:
        st.write("### Найденные товары:")
        for name, data in filtered.items():
            group_name = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
            article = data.get("article", data) if isinstance(data, dict) else data
            st.info(f"📁 [{group_name}] **{name}**  ➔  `Артикул: {article}`")
    else:
        st.warning("Товар не найден")
else:
    if products_db:
        # Панель выгрузки бэкапа доступна только в режиме просмотра администраторам (сделаем ниже),
        # а продавцам показываем просто папки
        for group, items in grouped_products.items():
            if items:
                with st.expander(f"📁 {group} ({len(items)} шт.)"):
                    for name, article in items.items():
                        st.write(f"• {name} ➔ `{article}`")

st.divider()

# 2. АВТОРИЗАЦИЯ И РАЗДЕЛЕНИЕ ПРАВ
st.subheader("🔐 Вход в систему управления")
user_password = st.text_input("Введите пароль сотрудника или директора:", type="password")

# ПРОВЕРКА РОЛИ 1: СТАРШИЙ ПРОДАВЕЦ (Только добавление)
if user_password == PASSWORD_STAFF:
    st.success("🔓 Доступ разрешен: Режим Старшего Продавца")
    st.subheader("➕ Добавить новый товар")
    
    group_mode = st.radio("Как указать группу товаров?", ["Выбрать существующую группу", "➕ Создать новую группу"], horizontal=True, key="staff_mode")
    if group_mode == "Выбрать существующую группу":
        selected_group = st.selectbox("Выберите группу для товара:", existing_groups, key="staff_select")
    else:
        selected_group = st.text_input("Введите название НАЗВАНИЕ НОВОЙ ГРУППЫ:", key="staff_input").strip()

    new_name = st.text_input("Название самого товара:", key="staff_name")
    new_article = st.text_input("Артикул товара:", key="staff_art")

    if st.button("Сохранить товар", type="primary", key="staff_btn"):
        if selected_group and new_name and new_article:
            try:
                payload = {new_name.strip(): {"group": selected_group, "article": new_article.strip()}}
                requests.patch(FIREBASE_URL, json=payload, timeout=3)
                st.success("Товар успешно добавлен!")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Ошибка сети")
        else:
            st.error("Заполните все поля!")

# ПРОВЕРКА РОЛИ 2: ДИРЕКТОР / АДМИНИСТРАТОР (Полный доступ + Редактирование + Бэкап)
elif user_password == PASSWORD_ADMIN:
    st.success("👑 Доступ разрешен: Полный режим Администратора")
    
    # Кнопка резервной копии Excel вынесена в админку для безопасности
    if products_db:
        raw_list = []
        for name, data in products_db.items():
            g = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
            art = data.get("article", data) if isinstance(data, dict) else data
            raw_list.append([g, name, art])
        df = pd.DataFrame(raw_list, columns=["Группа", "Название товара", "Артикул"])
        excel_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Скачать всю базу в Excel (Резервная копия)",
            data=excel_data,
            file_name="baza_artikulov.csv",
            mime="text/csv"
        )

    tab1, tab2, tab3 = st.tabs(["➕ Добавить товар", "✏️ Редактировать товар", "🗑️ Удалить товар / группу"])
    
    with tab1:
        st.subheader("Добавить новый товар")
        group_mode = st.radio("Как указать группу товаров?", ["Выбрать существующую группу", "➕ Создать новую группу"], horizontal=True, key="admin_mode")
        if group_mode == "Выбрать существующую группу":
            selected_group = st.selectbox("Выберите группу для товара:", existing_groups, key="admin_select")
        else:
            selected_group = st.text_input("Введите название НАЗВАНИЕ НОВОЙ ГРУППЫ:", key="admin_input").strip()

        new_name = st.text_input("Название самого товара:", key="admin_name")
        new_article = st.text_input("Артикул товара:", key="admin_art")

        if st.button("Сохранить и отправить всем", type="primary", key="admin_btn"):
            if selected_group and new_name and new_article:
                try:
                    payload = {new_name.strip(): {"group": selected_group, "article": new_article.strip()}}
                    requests.patch(FIREBASE_URL, json=payload, timeout=3)
                    st.success("Успешно добавлено!")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("Ошибка сети")

    with tab2:
        st.subheader("✏️ Изменить существующий товар без удаления")
        if products_db:
            edit_target = st.selectbox("Выберите товар для исправления:", ["-- Не выбрано --"] + sorted(list(products_db.keys())))
            
            if edit_target != "-- Не выбрано --":
                # Предзаполняем старые данные выбранного товара в поля ввода
                old_data = products_db[edit_target]
                old_group = old_data.get("group", "Без группы") if isinstance(old_data, dict) else "Без группы"
                old_article = old_data.get("article", old_data) if isinstance(old_data, dict) else old_data
                
                st.write(f"**Текущие данные:** Группа: *{old_group}*, Артикул: *{old_article}*")
                
                edit_group = st.selectbox("Изменить группу на:", all_groups, index=all_groups.index(old_group) if old_group in all_groups else 0)
                edit_name = st.text_input("Изменить название товара на:", value=edit_target)
                edit_article = st.text_input("Изменить артикул на:", value=old_article)
                
                if st.button("Сохранить изменения", type="primary"):
                    try:
                        # Если название поменялось, сначала удаляем старый ключ из базы
                        if edit_name.strip() != edit_target:
                            encoded_old_name = requests.utils.quote(edit_target)
                            DEL_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products/{encoded_old_name}.json"
                            requests.delete(DEL_URL, timeout=3)
                        
                        # Записываем обновленные данные
                        payload = {edit_name.strip(): {"group": edit_group, "article": edit_article.strip()}}
                        requests.patch(FIREBASE_URL, json=payload, timeout=3)
                        
                        st.success("Товар успешно обновлен у всех продавцов!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка сети: {e}")
        else:
            st.write("База данных пуста.")

    with tab3:
        st.subheader("Удалить старый товар")
        if products_db:
            delete_target = st.selectbox("Выберите товар для удаления:", ["-- Не выбрано --"] + sorted(list(products_db.keys())))
            if st.button("Удалить товар безвозвратно", type="secondary"):
                if delete_target != "-- Не выбрано --":
                    try:
                        encoded_name = requests.utils.quote(delete_target)
                        DEL_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products/{encoded_name}.json"
                        response = requests.delete(DEL_URL, timeout=3)
                        if response.status_code == 200:
                            st.success(f"Товар успешно удален!")
                            time.sleep(1)
                            st.rerun()
                    except:
                        st.error("Ошибка удаления")

else:
    if user_password != "":
        st.error("❌ Неверный пароль доступа!")
