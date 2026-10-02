import streamlit as st
import requests
import time
import pandas as pd

# Ссылка на вашу базу Firebase
PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products"

st.set_page_config(page_title="База Артикулов", page_icon="📦", layout="centered")
st.title("📦 База Артикулов по Группам")

def load_data():
    try:
        response = requests.get(f"{FIREBASE_URL}.json", timeout=3)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

products_db = load_data()

# СПИСОК ГРУПП ДЛЯ ВАШЕГО МАГАЗИНА (Вы можете добавлять сюда новые группы через запятую)
AVAILABLE_GROUPS = ["Конфеты", "Печенье", "Чай/Кофе", "Напитки", "Бакалея", "Разное"]

# 1. БЛОК ПОИСКА И ОТОБРАЖЕНИЯ ПО ГРУППАМ
st.subheader("🔍 Поиск и Просмотр")
search_query = st.text_input("Введите или наговорите название товара для быстрого поиска:")

if search_query:
    # Мгновенный поиск по всей базе
    filtered = {k: v for k, v in products_db.items() if search_query.lower() in k.lower()}
    if filtered:
        st.write("### Найденные товары:")
        for name, data in filtered.items():
            # Проверяем старый формат данных (если это была просто строка, а не словарь с группой)
            group_name = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
            article = data.get("article", data) if isinstance(data, dict) else data
            st.info(f"📁 [{group_name}] **{name}**  ➔  `Артикул: {article}`")
    else:
        st.warning("Товар не найден")
else:
    # Группируем товары для отображения в выпадающих спойлерах
    grouped_products = {g: {} for g in AVAILABLE_GROUPS + ["Без группы"]}
    
    if products_db:
        for name, data in products_db.items():
            if isinstance(data, dict):
                g = data.get("group", "Без группы")
                art = data.get("article", "")
            else:
                g = "Без группы"
                art = data
            if g not in grouped_products:
                grouped_products[g] = {}
            grouped_products[g][name] = art

        # Кнопка скачивания резервной копии в Excel
        raw_list = []
        for name, data in products_db.items():
            g = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
            art = data.get("article", data) if isinstance(data, dict) else data
            raw_list.append([g, name, art])
        
        df = pd.DataFrame(raw_list, columns=["Группа", "Название товара", "Артикул"])
        excel_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Скачать всю базу в Excel",
            data=excel_data,
            file_name="baza_artikulov.csv",
            mime="text/csv"
        )
        st.write("")

        # Создаем раскрывающиеся спойлеры для каждой группы товаров
        for group, items in grouped_products.items():
            if items: # Показываем группу только если в ней есть товары
                with st.expander(f"📁 {group} ({len(items)} шт.)"):
                    for name, article in items.items():
                        st.write(f"• {name} ➔ `{article}`")

st.divider()

# 2. БЛОК ДОБАВЛЕНИЯ ТОВАРА С ВЫБОРОМ ГРУППЫ
st.subheader("➕ Добавить новый товар")
new_group = st.selectbox("Выберите группу для товара:", AVAILABLE_GROUPS)
new_name = st.text_input("Название товара:")
new_article = st.text_input("Артикул:")

if st.button("Сохранить и отправить всем", type="primary"):
    if new_name and new_article:
        try:
            # Сохраняем в Firebase структуру: Название -> {группа, артикул}
            payload = {
                new_name.strip(): {
                    "group": new_group,
                    "article": new_article.strip()
                }
            }
            requests.patch(f"{FIREBASE_URL}.json", json=payload, timeout=3)
            st.success(f"Товар успешно добавлен в группу '{new_group}'!")
            time.sleep(1)
            st.rerun()
        except:
            st.error("Ошибка сети. Не удалось отправить.")
    else:
        st.error("Заполните название и артикул!")

st.divider()

# 3. БЛОК УДАЛЕНИЯ ТОВАРА
st.subheader("🗑️ Удалить старый товар")
if products_db:
    delete_target = st.selectbox("Выберите товар для удаления:", ["-- Не выбрано --"] + list(products_db.keys()))
    if st.button("Удалить безвозвратно", type="secondary"):
        if delete_target != "-- Не выбрано --":
            try:
                encoded_name = requests.utils.quote(delete_target)
                response = requests.delete(f"{FIREBASE_URL}/{encoded_name}.json", timeout=3)
                if response.status_code == 200:
                    st.success(f"Товар '{delete_target}' успешно удален!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")
