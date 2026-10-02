import streamlit as st
import requests
import time
import pandas as pd

# Ссылка на вашу базу Firebase
PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products.json"

st.set_page_config(page_title="База Артикулов", page_icon="📦")
st.title("📦 Поиск Артикулов")

def load_data():
    try:
        response = requests.get(FIREBASE_URL, timeout=3)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

products_db = load_data()

st.subheader("🔍 Поиск")
search_query = st.text_input("Введите или наговорите название товара:")

if search_query:
    filtered = {k: v for k, v in products_db.items() if search_query.lower() in k.lower()}
    if filtered:
        st.write("### Найденные товары:")
        for name, article in filtered.items():
            st.info(f"**{name}**  ➔  `Артикул: {article}`")
    else:
        st.warning("Товар не найден")
elif products_db:
    st.write("### Все товары в базе:")
    df = pd.DataFrame(list(products_db.items()), columns=["Название товара", "Артикул"])
    
    excel_data = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Скачать всю базу в Excel (Резервная копия)",
        data=excel_data,
        file_name="baza_artikulov.csv",
        mime="text/csv"
    )
    st.divider()
    
    for name, article in products_db.items():
        st.write(f"• {name} ➔ `{article}`")

st.divider()

st.subheader("➕ Добавить новый товар")
new_name = st.text_input("Название нового товара:")
new_article = st.text_input("Артикул нового товара:")

if st.button("Сохранить и отправить всем", type="primary"):
    if new_name and new_article:
        try:
            requests.patch(FIREBASE_URL, json={new_name.strip(): new_article.strip()}, timeout=3)
            st.success(f"Товар '{new_name}' успешно добавлен! Перезагрузите страницу.")
            time.sleep(1)
            st.rerun()
        except:
            st.error("Ошибка сети. Не удалось отправить.")
    else:
        st.error("Заполните оба поля!")
