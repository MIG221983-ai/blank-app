import streamlit as st
import requests
import time
import pandas as pd

# Ссылка на вашу базу Firebase
PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products.json"

# ВАШ СЕКРЕТНЫЙ ПАРОЛЬ ДЛЯ АДМИНКИ
ADMIN_PASSWORD = "1234"

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

# Собираем список групп, которые реально существуют в базе данных товаров
detected_groups = set()
if products_db:
    for data in products_db.values():
        if isinstance(data, dict):
            detected_groups.add(data.get("group", "Без группы"))
        else:
            detected_groups.add("Без группы")

# Если база совсем пустая, делаем базовый набор групп
if not detected_groups:
    detected_groups = {"Конфеты", "Печенье", "Чай/Кофе", "Разное"}

# Убираем "Без группы" из списка выбора при добавлении, чтобы не захламлять
existing_groups = sorted(list(detected_groups - {"Без группы"}))
if not existing_groups:
    existing_groups = ["Конфеты", "Печенье", "Чай/Кофе", "Разное"]

all_groups = sorted(list(detected_groups | {"Без группы"}))
grouped_products = {g: {} for g in all_groups}

# Распределяем товары по их группам
if products_db:
    for name, data in products_db.items():
        g = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
        art = data.get("article", data) if isinstance(data, dict) else data
        if g not in grouped_products:
            grouped_products[g] = {}
        grouped_products[g][name] = art

# 1. БЛОК ПОИСКА И ОТОБРАЖЕНИЯ ПО ГРУППАМ
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
        # Создание файла Excel для бэкапа
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
        st.write("")

        # Рисуем раскрывающиеся папки групп
        for group, items in grouped_products.items():
            if items:
                with st.expander(f"📁 {group} ({len(items)} шт.)"):
                    for name, article in items.items():
                        st.write(f"• {name} ➔ `{article}`")

st.divider()

# 2. БЛОК АДМИНИСТРАТОРА (ПОД ПАРОЛЕМ)
st.subheader("🔐 Режим Администратора")
user_password = st.text_input("Введите пароль, чтобы открыть инструменты управления:", type="password")

if user_password == ADMIN_PASSWORD:
    st.success("🔓 Доступ разрешен!")
    
    tab1, tab2 = st.tabs(["➕ Добавить товар / Создать группу", "🗑️ Удалить старый товар"])
    
    with tab1:
        st.subheader("Добавить новый товар")
        group_mode = st.radio("Как указать группу товаров?", ["Выбрать существующую группу", "➕ Создать новую группу"], horizontal=True)

        if group_mode == "Выбрать существующую группу":
            selected_group = st.selectbox("Выберите группу для товара:", existing_groups)
        else:
            selected_group = st.text_input("Введите название НАЗВАНИЕ НОВОЙ ГРУППЫ (например, 'Молочка'):").strip()

        new_name = st.text_input("Название самого товара:")
        new_article = st.text_input("Артикул товара:")

        if st.button("Сохранить и отправить всем", type="primary"):
            if not selected_group or selected_group == "":
                st.error("Укажите группу товаров!")
            elif not new_name or not new_article:
                st.error("Заполните название товара и артикул!")
            else:
                try:
                    payload = {new_name.strip(): {"group": selected_group, "article": new_article.strip()}}
                    requests.patch(FIREBASE_URL, json={"": ""}, timeout=1) # быстрая проверка сети
                    requests.patch(FIREBASE_URL, json=payload, timeout=3)
                    st.success(f"Успешно добавлено!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка сети: {e}")

    with tab2:
        st.subheader("Удалить старый товар")
        if products_db:
            delete_target = st.selectbox("Выберите товар для удаления:", ["-- Не выбрано --"] + list(products_db.keys()))
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
                    except Exception as e:
                        st.error(f"Ошибка удаления: {e}")
else:
    if user_password != "":
        st.error("❌ Неверный пароль администратора!")
