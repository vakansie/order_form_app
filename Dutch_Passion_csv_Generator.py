import csv
import sqlite3
from flask import Flask, render_template, request, send_file, jsonify, Response
from dataclasses import dataclass
import json

seeds_db =  r'products.db'
order_file = r'Dutch_Passion_Order.csv'
app = Flask(__name__)

@dataclass (frozen=True)
class Seed_Product:
    id: str
    name: str
    type: str
    pack_size: int
    wholesale_price: float
    retail_price: float
    manufacturer: str

class Order:
    def __init__(self) -> None:
        self.item_list: list[tuple[Seed_Product, int]] = []

    def write_to_file(self):
        with open(order_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for product, quantity in self.item_list:
                writer.writerow([product.id, quantity, 'STK'])

class Database_Service:
    def __init__(self, database) -> None:
        self.database = database
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_seeds_from_db(self) -> dict:
        self.cursor.execute('SELECT * FROM dutch_passion_seeds')
        rows = self.cursor.fetchall()
        seeds = {f'{seed_data[1]}{seed_data[3]}': Seed_Product(*seed_data) for seed_data in rows}
        return seeds

    def get_seed_by_id(self, seed_id:str)-> Seed_Product:
        if not seed_id.isdecimal(): return None
        self.cursor.execute('SELECT * FROM dutch_passion_seeds WHERE id = ?', (seed_id,))
        seed_data = self.cursor.fetchone()
        if not seed_data: return {seed_id: ' not found'}
        seed = Seed_Product(*seed_data)
        return seed

    def fetch_seed_data(self) -> tuple[list[str], list[int], dict[str: Seed_Product]]:
        self.cursor.execute("SELECT DISTINCT name FROM dutch_passion_seeds")
        seed_names = [row[0] for row in self.cursor.fetchall()]
        self.cursor.execute("SELECT DISTINCT pack_size FROM dutch_passion_seeds ORDER BY pack_size")
        pack_sizes = [row[0] for row in self.cursor.fetchall()]
        available_products = self.get_seeds_from_db()
        return seed_names, pack_sizes, available_products

    def search(self, query: str)-> list[Seed_Product]:
        self.cursor.execute("SELECT * FROM dutch_passion_seeds WHERE name LIKE ?", ('%' + query + '%',))
        results = self.cursor.fetchall()
        products = [Seed_Product(*product_data) for product_data in results]
        result = []
        for product in products:
            if product.name not in [product.name for product in result]:
                result.append(product)
        return result

    def search_attr(self, attr:str, query: str)-> list[Seed_Product]:
        self.cursor.execute("SELECT * FROM dutch_passion_seeds WHERE {} LIKE ?".format(attr), ('%' + query + '%',))
        results = self.cursor.fetchall()
        products = [Seed_Product(*product_data) for product_data in results]
        result = []
        for product in products:
            if product.name not in [product.name for product in result]:
                result.append(product)
        return result

    def add_column_to_table(self, table_name, column_name, value) ->dict:
        self.cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = self.cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        if column_name in existing_columns:
            return {'already exists:': str(column_name)}
        try:
            self.cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name}')
            self.cursor.execute(f'UPDATE {table_name} SET {column_name}=?', (value,))
            self.connection.commit()
            return {'success': f'Column {column_name} added to table {table_name} and filled with value {value}'}
        except sqlite3.Error as e:
            return {'error': str(e)}

@app.route('/', methods=['GET'])
def render_order_form() -> str:
    database_service = Database_Service(seeds_db)
    seed_names, pack_sizes, available_products = database_service.fetch_seed_data()
    return render_template('order_form.html', seed_names=seed_names, pack_sizes=pack_sizes, available_products=available_products)

@app.route('/download', methods=['GET'])
def download()  -> Response:
    return send_file(
        path_or_file=order_file,
        mimetype='text/csv',
        download_name='Dutch_Passion_Order.csv',
        as_attachment=True,
        max_age=0)

@app.route('/get_seed_by_id', methods=['GET'])
def get_seed_by_id_route()-> Response:
    id = request.args.get('seed_id')
    database_service = Database_Service(seeds_db)
    seed = database_service.get_seed_by_id(id)
    return jsonify(seed)

@app.route('/create_file', methods=['GET'])
def order_form() -> Response:
    database_service = Database_Service(seeds_db)
    ordered_products = json.loads(request.args.get('order_data'))
    order = Order()
    for id, quantity_ordered in ordered_products.items():
        if not isinstance(quantity_ordered, int): continue
        product = database_service.get_seed_by_id(id)
        if not product: continue
        order.item_list.append((product, quantity_ordered))
    order.write_to_file()
    return jsonify({str(product): qty for (product, qty) in order.item_list})

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query: return jsonify([])
    database_service = Database_Service(seeds_db)
    results = database_service.search(query=query)
    return jsonify(results)

@app.route('/search_attr', methods=['GET'])
def search_attr():
    query = request.args.get('query')
    if not query: return {}
    attr = 'id' if len(query) in (4, 5) and query.isdecimal() else 'name'
    database_service = Database_Service(seeds_db)
    results = database_service.search_attr(attr=attr, query=query)
    return jsonify(results)

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()