"""
Воронка интернет-магазина косметики: дешёвые и дорогие товары.

Данные: Kaggle, "eCommerce Events History in Cosmetics Shop", файл 2019-Dec.csv
Вопрос: одинаково ли ведут себя покупатели дешёвых и дорогих товаров
на пути просмотр -> корзина -> покупка, и кто приносит больше выручки?

Запуск: положите 2019-Dec.csv рядом со скриптом и выполните python analysis.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_PATH = Path("2019-Dec.csv")
IMAGES_DIR = Path("images")


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def unique_users(data: pd.DataFrame, event_type: str) -> int:
    """Сколько уникальных пользователей хотя бы раз сделали событие event_type."""
    return data.loc[data["event_type"] == event_type, "user_id"].nunique()


def funnel(data: pd.DataFrame) -> dict:
    """Воронка по уникальным пользователям: просмотр -> корзина -> покупка."""
    views = unique_users(data, "view")
    carts = unique_users(data, "cart")
    purchases = unique_users(data, "purchase")
    return {
        "view": views,
        "cart": carts,
        "purchase": purchases,
        "view_to_cart": carts / views,
        "cart_to_purchase": purchases / carts,
    }


def revenue_stats(data: pd.DataFrame) -> dict:
    """Выручка, число покупок и средний чек (на один товар) по событиям purchase."""
    purchases = data[data["event_type"] == "purchase"]
    revenue = purchases["price"].sum()
    count = len(purchases)
    return {"revenue": revenue, "purchases": count, "avg_check": revenue / count}


# ---------------------------------------------------------------------------
# 1. Загрузка и первичная проверка данных
# ---------------------------------------------------------------------------

df = pd.read_csv(DATA_PATH)

print("Строк и столбцов:", df.shape)
print("\nСобытий каждого типа:")
print(df["event_type"].value_counts())
print("\nПропуски по колонкам:")
print(df.isna().sum())

# ---------------------------------------------------------------------------
# 2. Аномальные цены: нулевые и отрицательные
# ---------------------------------------------------------------------------

zero_priced = df[df["price"] == 0]
negative_priced = df[df["price"] < 0]

print("\nСтрок с нулевой ценой:", len(zero_priced))
print("Строк с отрицательной ценой:", len(negative_priced))
print("Покупок среди нулевых цен:", unique_users(zero_priced, "purchase"))
print("Типы событий с отрицательной ценой:")
print(negative_priced["event_type"].value_counts())

# Исключаем нулевые и отрицательные цены из анализа по ценовым группам
clean = df[df["price"] > 0]
print("\nПосле исключения аномальных цен строк:", len(clean))

# ---------------------------------------------------------------------------
# 3. Общая воронка за месяц (по всем данным, как есть)
# ---------------------------------------------------------------------------

overall = funnel(df)
print("\nОбщая воронка (уникальные пользователи):")
print(f"  просмотр: {overall['view']}, корзина: {overall['cart']}, покупка: {overall['purchase']}")
print(f"  просмотр -> корзина: {overall['view_to_cart']:.3f}")
print(f"  корзина -> покупка:  {overall['cart_to_purchase']:.3f}")

# ---------------------------------------------------------------------------
# 4. Деление товаров на дешёвые и дорогие по медиане цены
#    Медиана, а не среднее: распределение цен с длинным хвостом дорогих товаров
# ---------------------------------------------------------------------------

median_price = clean["price"].median()
mean_price = clean["price"].mean()
print(f"\nМедиана цены: {median_price:.2f}, среднее: {mean_price:.2f}")

low_price = clean[clean["price"] < median_price]
high_price = clean[clean["price"] >= median_price]
print("Событий в группе дешёвых:", len(low_price))
print("Событий в группе дорогих:", len(high_price))

# ---------------------------------------------------------------------------
# 5. Воронка по группам
# ---------------------------------------------------------------------------

low_funnel = funnel(low_price)
high_funnel = funnel(high_price)

print("\nВоронка, дешёвые:  просмотр -> корзина {:.3f}, корзина -> покупка {:.3f}".format(
    low_funnel["view_to_cart"], low_funnel["cart_to_purchase"]))
print("Воронка, дорогие:  просмотр -> корзина {:.3f}, корзина -> покупка {:.3f}".format(
    high_funnel["view_to_cart"], high_funnel["cart_to_purchase"]))

# ---------------------------------------------------------------------------
# 6. Выручка по группам
# ---------------------------------------------------------------------------

low_rev = revenue_stats(low_price)
high_rev = revenue_stats(high_price)

total_revenue = low_rev["revenue"] + high_rev["revenue"]
total_purchases = low_rev["purchases"] + high_rev["purchases"]

print("\nДешёвые: выручка {:.0f}, покупок {}, средний чек {:.2f}".format(
    low_rev["revenue"], low_rev["purchases"], low_rev["avg_check"]))
print("Дорогие: выручка {:.0f}, покупок {}, средний чек {:.2f}".format(
    high_rev["revenue"], high_rev["purchases"], high_rev["avg_check"]))

high_revenue_share = high_rev["revenue"] / total_revenue
high_purchases_share = high_rev["purchases"] / total_purchases
print(f"Доля дорогих в выручке: {high_revenue_share:.1%}")
print(f"Доля дорогих в числе покупок: {high_purchases_share:.1%}")

# Сверка: покупки в группах + покупки с аномальной ценой должны дать все покупки
all_purchases = (df["event_type"] == "purchase").sum()
print("\nСверка покупок: в группах {}, всего {}, разница {}".format(
    total_purchases, all_purchases, all_purchases - total_purchases))

# ---------------------------------------------------------------------------
# 7. Графики
# ---------------------------------------------------------------------------

IMAGES_DIR.mkdir(exist_ok=True)

# 7.1 Воронка по группам
fig, ax = plt.subplots(figsize=(7, 4.5))
steps = ["Просмотр → корзина", "Корзина → покупка"]
low_vals = [low_funnel["view_to_cart"], low_funnel["cart_to_purchase"]]
high_vals = [high_funnel["view_to_cart"], high_funnel["cart_to_purchase"]]
x = range(len(steps))
width = 0.35
bars_low = ax.bar([i - width / 2 for i in x], low_vals, width, label="Дешёвые")
bars_high = ax.bar([i + width / 2 for i in x], high_vals, width, label="Дорогие")
ax.bar_label(bars_low, labels=[f"{v:.1%}" for v in low_vals])
ax.bar_label(bars_high, labels=[f"{v:.1%}" for v in high_vals])
ax.set_xticks(list(x))
ax.set_xticklabels(steps)
ax.set_ylabel("Доля уникальных пользователей")
ax.set_title("Воронка по ценовым группам")
ax.legend()
fig.tight_layout()
fig.savefig(IMAGES_DIR / "funnel_by_price_group.png", dpi=150)
plt.close(fig)

# 7.2 Доля дорогих товаров в покупках и в выручке
fig, ax = plt.subplots(figsize=(6, 4.5))
labels = ["Доля в числе покупок", "Доля в выручке"]
values = [high_purchases_share, high_revenue_share]
bars = ax.bar(labels, values, color="tab:orange")
ax.bar_label(bars, labels=[f"{v:.1%}" for v in values])
ax.set_ylim(0, 1)
ax.set_ylabel("Доля дорогих товаров")
ax.set_title("Дорогие товары: покупки и выручка")
fig.tight_layout()
fig.savefig(IMAGES_DIR / "revenue_vs_purchases.png", dpi=150)
plt.close(fig)

print("\nГрафики сохранены в папку", IMAGES_DIR)
