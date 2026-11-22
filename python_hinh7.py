
# ================================================================
# DO AN CUOI KY - CO SO DU LIEU
# E-COMMERCE & CLICKSTREAM ANALYTICS
#
# MYSQL + MONGODB + PYTHON
#
# MySQL:
#   ecommerce_clickstream
#
# MongoDB:
#   ecommerce_clickstream_analytics
#
# Collections:
#   product_catalog
#   shopping_sessions
#   clickstream_events
#
# Du lieu demo:
#   150 products
#   40 sessions
#   360 clickstream events
# ================================================================

import os
import random
from datetime import datetime, timedelta, timezone

import mysql.connector
from pymongo import MongoClient, ASCENDING, DESCENDING


# ================================================================
# 1. CAU HINH HE THONG
# ================================================================

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD", "0510200726012007@QB2k7"),
    "database": "ecommerce_clickstream"
}

MONGO_URI = "mongodb://127.0.0.1:27017"

MONGO_DATABASE = "ecommerce_clickstream_analytics"

random.seed(42)


# ================================================================
# 2. KET NOI MYSQL
# ================================================================

def connect_mysql():

    print("\n[MYSQL] Dang ket noi...")

    connection = mysql.connector.connect(**MYSQL_CONFIG)

    print("[OK] Ket noi MySQL thanh cong!")

    return connection


# ================================================================
# 3. KET NOI MONGODB
# ================================================================

def connect_mongodb():

    print("\n[MONGODB] Dang ket noi...")

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    database = client[MONGO_DATABASE]

    print("[OK] Ket noi MongoDB thanh cong!")

    return client, database


# ================================================================
# 4. LAY DU LIEU SAN PHAM TU MYSQL
# ================================================================

def get_products_from_mysql(connection):

    sql = """
        SELECT
            p.product_id,
            p.category_id,
            p.brand_id,
            p.sku,
            p.product_name,
            p.description,
            p.price,
            p.stock_quantity,
            p.status,
            c.category_name,
            b.brand_name

        FROM products AS p

        JOIN categories AS c
            ON p.category_id = c.category_id

        JOIN brands AS b
            ON p.brand_id = b.brand_id

        ORDER BY p.product_id
    """

    cursor = connection.cursor(dictionary=True)

    cursor.execute(sql)

    products = cursor.fetchall()

    cursor.close()

    return products


# ================================================================
# 5. LAY DU LIEU KHACH HANG TU MYSQL
# ================================================================

def get_customers_from_mysql(connection):

    sql = """
        SELECT
            customer_id,
            full_name,
            email
        FROM customers
        ORDER BY customer_id
    """

    cursor = connection.cursor(dictionary=True)

    cursor.execute(sql)

    customers = cursor.fetchall()

    cursor.close()

    return customers


# ================================================================
# 6. TAO INDEX MONGODB
# ================================================================

def create_indexes(database):

    database.product_catalog.create_index(
        [("product_id", ASCENDING)],
        unique=True
    )

    database.shopping_sessions.create_index(
        [("session_id", ASCENDING)],
        unique=True
    )

    database.clickstream_events.create_index(
        [("event_time", DESCENDING)]
    )

    database.clickstream_events.create_index(
        [("product_id", ASCENDING)]
    )

    database.clickstream_events.create_index(
        [("session_id", ASCENDING)]
    )

    print("[OK] Da tao cac MongoDB indexes!")


# ================================================================
# 7. DONG BO PRODUCT CATALOG
# ================================================================

def seed_product_catalog(database, products):

    collection = database.product_catalog

    current_count = collection.count_documents({})

    if current_count > 0:

        print(
            f"[INFO] product_catalog da co "
            f"{current_count} documents. Khong nap lai."
        )

        return

    documents = []

    for product in products:

        documents.append({

            "product_id": str(product["product_id"]),

            "sku": product["sku"],

            "product_name": product["product_name"],

            "description": product["description"],

            "category": {
                "category_id": str(product["category_id"]),
                "category_name": product["category_name"]
            },

            "brand": {
                "brand_id": str(product["brand_id"]),
                "brand_name": product["brand_name"]
            },

            "price": product["price"],

            "stock_quantity": product["stock_quantity"],

            "status": product["status"],

            "source": "MySQL"
        })

    if documents:

        collection.insert_many(documents)

    print(
        f"[OK] Da dong bo {len(documents)} san pham "
        "vao MongoDB!"
    )


# ================================================================
# 8. TAO 40 PHIEN MUA SAM
# ================================================================

def seed_shopping_sessions(database, customers):

    collection = database.shopping_sessions

    current_count = collection.count_documents({})

    if current_count > 0:

        print(
            f"[INFO] shopping_sessions da co "
            f"{current_count} documents. Khong tao lai."
        )

        return

    if not customers:

        raise ValueError("Khong tim thay khach hang trong MySQL.")

    documents = []

    devices = [
        "Desktop",
        "Mobile",
        "Tablet"
    ]

    now = datetime.now(timezone.utc)

    for i in range(1, 41):

        customer = customers[(i - 1) % len(customers)]

        start_time = now - timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23)
        )

        documents.append({

            "session_id": f"SES-{i:04d}",

            "customer_id": str(customer["customer_id"]),

            "customer_name": customer["full_name"],

            "device": random.choice(devices),

            "started_at": start_time,

            "session_status": "COMPLETED"
        })

    collection.insert_many(documents)

    print("[OK] Da tao 40 shopping sessions!")


# ================================================================
# 9. TAO 360 SU KIEN CLICKSTREAM
# ================================================================

def seed_clickstream_events(database, products, customers):

    collection = database.clickstream_events

    current_count = collection.count_documents({})

    if current_count > 0:

        print(
            f"[INFO] clickstream_events da co "
            f"{current_count} documents. Khong tao lai."
        )

        return

    if not products or not customers:

        raise ValueError(
            "Can co du lieu san pham va khach hang."
        )

    events = []

    event_types = [
        "product_view",
        "add_to_cart"
    ]

    weights = [0.75, 0.25]

    now = datetime.now(timezone.utc)

    # 40 sessions x 9 events = 360 events

    for session_number in range(1, 41):

        session_id = f"SES-{session_number:04d}"

        customer = customers[
            (session_number - 1) % len(customers)
        ]

        session_start = now - timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 20)
        )

        for event_number in range(1, 10):

            product = random.choice(products)

            event_type = random.choices(
                event_types,
                weights=weights,
                k=1
            )[0]

            event_time = session_start + timedelta(
                minutes=event_number * random.randint(1, 5)
            )

            events.append({

                "event_id": (
                    f"EVT-{session_number:04d}-"
                    f"{event_number:02d}"
                ),

                "session_id": session_id,

                "customer_id": str(customer["customer_id"]),

                "product_id": str(product["product_id"]),

                "event_type": event_type,

                "event_time": event_time,

                "page_url": (
                    "/products/"
                    + str(product["product_id"])
                )
            })

    collection.insert_many(events)

    print("[OK] Da tao 360 clickstream events!")


# ================================================================
# 10. KHOI TAO DU LIEU MONGODB NEU COLLECTION TRONG
# ================================================================

def initialize_mongodb(connection, database):

    print("\n" + "=" * 65)

    print("KHOI TAO DU LIEU MONGODB")

    print("=" * 65)

    products = get_products_from_mysql(connection)

    customers = get_customers_from_mysql(connection)

    print(f"So san pham MySQL: {len(products)}")

    print(f"So khach hang MySQL: {len(customers)}")

    if not products:
        raise ValueError(
            "MySQL khong co san pham. "
            "Hay chay mysql_all_in_one.sql truoc."
        )

    if not customers:
        raise ValueError(
            "MySQL khong co khach hang."
        )

    create_indexes(database)

    seed_product_catalog(database, products)

    seed_shopping_sessions(database, customers)

    seed_clickstream_events(
        database,
        products,
        customers
    )

    return products


# ================================================================
# 11. KIEM TRA DU LIEU MONGODB
# ================================================================

def check_mongodb_data(database):

    print("\n" + "=" * 65)

    print("KIEM TRA DU LIEU MONGODB")

    print("=" * 65)

    counts = {

        "Product Catalog":
            database.product_catalog.count_documents({}),

        "Shopping Sessions":
            database.shopping_sessions.count_documents({}),

        "Clickstream Events":
            database.clickstream_events.count_documents({})
    }

    for name, count in counts.items():

        print(f"{name}: {count}")

    return counts


# ================================================================
# 12. TRUY VAN CLICKSTREAM BANG AGGREGATE
# ================================================================

def get_clickstream_statistics(database):

    collection = database.clickstream_events

    start_date = datetime.now(timezone.utc) - timedelta(
        days=30
    )

    pipeline = [

        {
            "$match": {

                "event_time": {
                    "$gte": start_date
                },

                "event_type": {
                    "$in": [
                        "product_view",
                        "add_to_cart"
                    ]
                }
            }
        },

        {
            "$group": {

                "_id": "$product_id",

                "view_count": {

                    "$sum": {

                        "$cond": [

                            {
                                "$eq": [
                                    "$event_type",
                                    "product_view"
                                ]
                            },

                            1,

                            0
                        ]
                    }
                },

                "cart_add_count": {

                    "$sum": {

                        "$cond": [

                            {
                                "$eq": [
                                    "$event_type",
                                    "add_to_cart"
                                ]
                            },

                            1,

                            0
                        ]
                    }
                }
            }
        },

        {
            "$sort": {

                "view_count": -1,

                "cart_add_count": -1
            }
        },

        {
            "$limit": 15
        }
    ]

    return list(collection.aggregate(pipeline))


# ================================================================
# 13. TRUY VAN MYSQL BANG SELECT
# ================================================================

def get_mysql_product_details(connection, product_ids):

    if not product_ids:

        return []

    placeholders = ", ".join(
        ["%s"] * len(product_ids)
    )

    sql = f"""

        SELECT

            p.product_id,

            p.sku,

            p.product_name,

            p.price,

            p.stock_quantity,

            p.status,

            c.category_name,

            b.brand_name

        FROM products AS p

        JOIN categories AS c

            ON p.category_id = c.category_id

        JOIN brands AS b

            ON p.brand_id = b.brand_id

        WHERE p.product_id IN ({placeholders})

    """

    cursor = connection.cursor(dictionary=True)

    cursor.execute(sql, tuple(product_ids))

    results = cursor.fetchall()

    cursor.close()

    return results


# ================================================================
# 14. TICH HOP MYSQL VA MONGODB
# ================================================================

def integrate_databases(connection, database):

    print("\nDANG TRUY VAN VA TICH HOP DU LIEU...")

    # MongoDB: thong ke hanh vi.
    behavior_data = get_clickstream_statistics(
        database
    )

    if not behavior_data:

        print("Khong tim thay du lieu clickstream.")

        return []

    product_ids = [

        str(item["_id"])

        for item in behavior_data

    ]

    # MySQL: lay thong tin san pham.
    mysql_data = get_mysql_product_details(
        connection,
        product_ids
    )

    product_lookup = {

        str(item["product_id"]): item

        for item in mysql_data

    }

    integrated_results = []

    for behavior in behavior_data:

        product_id = str(behavior["_id"])

        product = product_lookup.get(product_id)

        if product is None:

            continue

        view_count = behavior["view_count"]

        cart_count = behavior["cart_add_count"]

        # Cong thuc diem quan tam.
        interest_score = view_count + cart_count * 3

        integrated_results.append({

            "product_id": product["product_id"],

            "sku": product["sku"],

            "product_name": product["product_name"],

            "category_name": product["category_name"],

            "brand_name": product["brand_name"],

            "price": product["price"],

            "stock_quantity": product["stock_quantity"],

            "view_count": view_count,

            "cart_add_count": cart_count,

            "interest_score": interest_score
        })

    integrated_results.sort(

        key=lambda item: item["interest_score"],

        reverse=True
    )

    return integrated_results


# ================================================================
# 15. HIEN THI KET QUA
# ================================================================

def display_results(results):

    print("\n")

    print("=" * 125)

    print("          TICH HOP MYSQL + MONGODB")

    print("          E-COMMERCE & CLICKSTREAM ANALYTICS")

    print("          TOP SAN PHAM DUOC QUAN TAM")

    print("=" * 125)

    if not results:

        print("Khong co ket qua de hien thi.")

        return

    print(

        f"{'PRODUCT ID':<12}"

        f"{'PRODUCT NAME':<30}"

        f"{'CATEGORY':<23}"

        f"{'BRAND':<15}"

        f"{'PRICE':>13}"

        f"{'VIEWS':>8}"

        f"{'CART':>8}"

        f"{'SCORE':>8}"

    )

    print("-" * 125)

    for item in results:

        print(

            f"{str(item['product_id']):<12}"

            f"{item['product_name'][:28]:<30}"

            f"{item['category_name'][:21]:<23}"

            f"{item['brand_name'][:13]:<15}"

            f"{item['price']:>13,}"

            f"{item['view_count']:>8}"

            f"{item['cart_add_count']:>8}"

            f"{item['interest_score']:>8}"

        )

    print("-" * 125)

    total_views = sum(

        item["view_count"]

        for item in results

    )

    total_cart = sum(

        item["cart_add_count"]

        for item in results

    )

    print(f"Tong san pham duoc xep hang: {len(results)}")

    print(f"Tong luot xem trong ket qua: {total_views}")

    print(f"Tong luot them gio trong ket qua: {total_cart}")

    print("=" * 125)

    print("\nHOAN THANH TICH HOP DU LIEU!")


# ================================================================
# 16. CHUONG TRINH CHINH
# ================================================================

def main():

    mysql_connection = None

    mongo_client = None

    try:

        # 1. Ket noi MySQL.
        mysql_connection = connect_mysql()

        # 2. Ket noi MongoDB.
        mongo_client, mongo_database = connect_mongodb()

        # 3. Khoi tao MongoDB neu du lieu dang trong.
        initialize_mongodb(
            mysql_connection,
            mongo_database
        )

        # 4. Kiem tra so luong document.
        check_mongodb_data(mongo_database)

        # 5. Truy van va tich hop hai database.
        results = integrate_databases(
            mysql_connection,
            mongo_database
        )

        # 6. Hien thi ket qua.
        display_results(results)

    except mysql.connector.Error as error:

        print("\n[MYSQL ERROR]", error)

    except Exception as error:

        print("\n[SYSTEM ERROR]", error)

    finally:

        if mysql_connection is not None:

            mysql_connection.close()

            print("\n[OK] Da dong ket noi MySQL.")

        if mongo_client is not None:

            mongo_client.close()

            print("[OK] Da dong ket noi MongoDB.")


# ================================================================
# 17. RUN PROGRAM
# ================================================================

if __name__ == "__main__":

    main()
