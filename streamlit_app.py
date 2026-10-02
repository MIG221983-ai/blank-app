import streamlit as st
import requests
import time
import pandas as pd

# Ссылки на вашу базу Firebase
PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app"
PRODUCTS_URL = f"{FIREBASE_URL}/products"
GROUPS_URL = f"{FIREBASE_URL}/custom_groups"

st.set_page_config(page_title="База Артикулов", page_icon="📦", layout="centered")
st.title("📦 База Артикулов по Группам")

# Функция загрузки товаров
def load_data():
    try:
        response = requests.get(f"{PRODUCTS_URL}.json", timeout=3)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

# Функция загрузки созданных пользователем групп
def load_groups():
    try:
        response = requests.get(f"{GROUPS_URL}.json", timeout=3)
        if response.status_code == 200 and response.json():
            return list(response.json().keys())
    except:
        pass
    # Базовые группы по умолчанию, если в базе еще ничего нет
    return ["Конфеты", "Печенье", "Чай/Кофе", "Разное"]

products_db = load_data()
saved_groups = load_groups()

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
    # Динамически собираем список всех групп, которые есть и в шаблоне, и у товаров в базе
    all_groups = sorted(list(set(saved_groups + ["Без группы"])))
    grouped_products = {g: {} for g in all_groups}
    
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

        # Кнопка Excel
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

        # Создаем раскрывающиеся папки
        for group, items in grouped_products.items():
            if items:
                with st.expander(f"📁 {group} ({len(items)} шт.)"):
                    for name, article in items.items():
                        st.write(f"• {name} ➔ `{article}`")

st.divider()

# 2. БЛОК ДОБАВЛЕНИЯ ТОВАРА И СОЗДАНИЯ ГРУПП
st.subheader("➕ Добавить новый товар / Создать группу")

# Выбор режима работы с группами
group_mode = st.radio("Как указать группу товаров?", ["Выбрать существующую группу", "➕ Создать новую группу"], horizontal=True)

if group_mode == "Выбрать существующую группу":
    selected_group = st.selectbox("Выберите группу для товара:", saved_groups)
else:
    selected_group = st.text_input("Введите название НАЗВАНИЕ НОВОЙ ГРУППЫ (например, Молочка):").strip()

new_name = st.text_input("Название самого товара (например, Сметана 15%):")
new_article = st.text_input("Артикул товара:")

if st.button("Сохранить и отправить всем", type="primary"):
    if not selected_group or selected_group == "":
        st.error("Укажите название группы или создайте новую!")
    elif not new_name or not new_article:
        st.error("Заполните название товара и его артикул!")
    else:
        try:
            # 1. Если группа новая — сохраняем её имя в список групп в Firebase
            if group_mode == "➕ Создать новую группу":
                requests.patch(f"{GROUPS_URL}.json", json={selected_group: True}, timeout=3)
            
            # 2. Сохраняем сам товар с привязкой к этой группе
            payload = {
                new_name.strip(): {
                    "group": selected_group,
                    "article": new_article.strip()
                }
            }
            requests.patch(f"{PRODUCTS_URL}.json", json=payload, timeout=3)
            
            st.success(f"Успешно! Товар добавлен в группу '{selected_group}'.")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка сети при отправке: {e}")

st.divider()

# 3. БЛОК УДАЛЕНИЯ ТОВАРА
st.subheader("🗑️ Удалить старый товар")
if products_db:
    delete_target = st.selectbox("Выберите товар для удаления:", ["-- Не выбрано --"] + list(products_db.keys()))
    if st.button("Удалить безвозвратно", type="secondary"):
        if delete_target != "-- Не выбрано --":
            try:
                encoded_name = requests.utils.quote(delete_target)
                response = requests.delete(f"{PRODUCTS_URL}/{encoded_name}.json", timeout=3)
                if response.status_code == 200:
                    st.success(f"Товар '{delete_target}' успешно удален!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")
