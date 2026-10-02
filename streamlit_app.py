import streamlit as st
import requests
import time
import pandas as pd

# Ссылки на вашу базу Firebase
PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app"
PRODUCTS_URL = f"{FIREBASE_URL}/products"
GROUPS_URL = f"{FIREBASE_URL}/custom_groups"

# ВАШ СЕКРЕТНЫЙ ПАРОЛЬ ДЛЯ АДМИНКИ (Вы можете заменить цифры '1234' на любые свои!)
ADMIN_PASSWORD = "0808"

st.set_page_config(page_title="База Артикулов", page_icon="📦", layout="centered")
st.title("📦 Умная База Артикулов")

def load_data():
    try:
        response = requests.get(f"{PRODUCTS_URL}.json", timeout=3)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

def load_groups():
    try:
        response = requests.get(f"{GROUPS_URL}.json", timeout=3)
        if response.status_code == 200 and response.json():
            return sorted(list(response.json().keys()))
    except:
        pass
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
    all_groups = sorted(list(set(saved_groups + ["Без группы"])))
    grouped_products = {g: {} for g in all_groups}
    
    if products_db:
        for name, data in products_db.items():
            g = data.get("group", "Без группы") if isinstance(data, dict) else "Без группы"
            art = data.get("article", data) if isinstance(data, dict) else data
            if g not in grouped_products:
                grouped_products[g] = {}
            grouped_products[g][name] = art

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

        for group, items in grouped_products.items():
            if items:
                with st.expander(f"📁 {group} ({len(items)} шт.)"):
                    for name, article in items.items():
                        st.write(f"• {name} ➔ `{article}`")

st.divider()

# ПОЛЕ ВВОДА ПАРОЛЯ ДЛЯ ДЕЙСТВИЙ (Новая защита!)
st.subheader("🔐 Режим Администратора")
user_password = st.text_input("Введите пароль, чтобы добавлять, изменять или удалять товары:", type="password")

# Проверяем, правильный ли пароль ввел пользователь
if user_password == ADMIN_PASSWORD:
    st.success("🔓 Доступ разрешен! Вам открыты инструменты управления базой:")

    # 2. БЛОК ДОБАВЛЕНИЯ ТОВАРА И СОЗДАНИЯ ГРУПП
    st.subheader("➕ Добавить новый товар")
    group_mode = st.radio("Как указать группу товаров?", ["Выбрать существующую группу", "➕ Создать новую группу"], horizontal=True)

    if group_mode == "Выбрать существующую группу":
        selected_group = st.selectbox("Выберите группу для товара:", saved_groups, key="add_box")
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
                if group_mode == "➕ Создать новую группу":
                    requests.patch(f"{GROUPS_URL}.json", json={selected_group: True}, timeout=3)
                payload = {new_name.strip(): {"group": selected_group, "article": new_article.strip()}}
                requests.patch(f"{PRODUCTS_URL}.json", json=payload, timeout=3)
                st.success(f"Успешно добавлено в группу '{selected_group}'!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка сети: {e}")

    st.divider()

    # 3. БЛОК УПРАВЛЕНИЯ ГРУППАМИ
    st.subheader("🛠️ Управление группами (Удаление / Переименование)")
    edit_group_target = st.selectbox("Выберите группу для изменения или удаления:", ["-- Не выбрано --"] + saved_groups)

    if edit_group_target != "-- Не выбрано --":
        action = st.radio("Что сделать с группой?", ["Переименовать старую группу", "Удалить группу полностью"])
        
        if action == "Переименовать старую группу":
            new_group_name = st.text_input(f"Введите новое название для группы '{edit_group_target}':").strip()
            if st.button("Применить переименование", type="primary"):
                if new_group_name:
                    try:
                        requests.patch(f"{GROUPS_URL}.json", json={new_group_name: True}, timeout=3)
                        requests.delete(f"{GROUPS_URL}/{requests.utils.quote(edit_group_target)}.json", timeout=3)
                        update_payload = {}
                        for name, data in products_db.items():
                            if isinstance(data, dict) and data.get("group") == edit_group_target:
                                update_payload[name] = {"group": new_group_name, "article": data.get("article", "")}
                        if update_payload:
                            requests.patch(f"{PRODUCTS_URL}.json", json=update_payload, timeout=3)
                        st.success("Группа успешно переименована везде!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка сети: {e}")
                else:
                    st.error("Введите новое название!")
                    
        elif action == "Удалить группу полностью":
            st.warning(f"Внимание! Группа '{edit_group_target}' исчезнет. Товары перенесутся в раздел 'Без группы'.")
            if st.button("Да, удалить группу безвозвратно"):
                try:
                    requests.delete(f"{GROUPS_URL}/{requests.utils.quote(edit_group_target)}.json", timeout=3)
                    update_payload = {}
                    for name, data in products_db.items():
                        if isinstance(data, dict) and data.get("group") == edit_group_target:
                            update_payload[name] = {"group": "Без группы", "article": data.get("article", "")}
                    if update_payload:
                        requests.patch(f"{PRODUCTS_URL}.json", json=update_payload, timeout=3)
                    st.success("Группа удалена!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка: {e}")

    st.divider()

    # 4. БЛОК УДАЛЕНИЯ ТОВАРА
    st.subheader("🗑️ Удалить старый товар")
    if products_db:
        delete_target = st.selectbox("Выберите товар для удаления:", ["-- Не выбрано --"] + list(products_db.keys()))
        if st.button("Удалить товар безвозвратно", type="secondary"):
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
else:
    if user_password != "":
        st.error("❌ Неверный пароль администратора! Инструменты изменения базы заблокированы.")
