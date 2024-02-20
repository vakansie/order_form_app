import csv
import sqlite3
from flask import Flask, render_template, request, send_file, jsonify

seeds_db = 'seeds.db'
order_file = 'Dutch_Passion_Order.csv'
app = Flask(__name__)
app.secret_key = 'asdasdasd'

class Seed_Product:
    def __init__(self, name, pack_size, id, type='', amount=0) -> None:
        self.name = name
        self.pack_size = pack_size
        self.id = id
        self.type = type
        self.amount = amount

    def __repr__(self) -> str:
        return f'{self.name} - {self.id} - {self.amount} - {self.pack_size}-pack{'s' if int(self.amount) > 1 else ''}'

class Database_Service:
    def __init__(self, database) -> None:
        self.database = database
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_seeds_from_db(self) -> dict:
        self.cursor.execute('SELECT name, pack_size, id, type FROM seeds')
        rows = self.cursor.fetchall()
        seeds = {f'{name}{pack_size}': Seed_Product(name, pack_size, id, type) for name, pack_size, id, type in rows}
        return seeds
    
    def get_code(self, name, pack_size):
        self.cursor.execute('SELECT id FROM seeds WHERE name = ? AND pack_size = ?', (name, pack_size,))
        response = self.cursor.fetchone()
        if not response: return None
        code = response[0]
        return code
    
    def fetch_seed_data(self):
        self.cursor.execute("SELECT DISTINCT name FROM seeds")
        seed_names = [row[0] for row in self.cursor.fetchall()]
        self.cursor.execute("SELECT DISTINCT pack_size FROM seeds ORDER BY pack_size")
        pack_sizes = [row[0] for row in self.cursor.fetchall()]
        available_products = self.get_seeds_from_db()
        self.connection.close()
        return seed_names, pack_sizes, available_products

    def get_seed(self):
        name = request.args.get('name')
        pack_size = request.args.get('pack_size')
        self.cursor.execute('SELECT * FROM seeds WHERE name=? AND pack_size=?', (name, pack_size))
        row = self.cursor.fetchone()
        if row:
            seed = {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'pack_size': row[3],
                'wholesale_price': row[4],
                'retail_price': row[5],
                'manufacturer': row[6]
            }
            return jsonify(seed)

    def add_column_to_table(self, table_name, column_name, value):
        self.cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = self.cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        if column_name in existing_columns:
            return {'already exists:': str(column_name)}
        try:
            self.cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name}')
            # Fill the column with the specified value for all rows
            self.cursor.execute(f'UPDATE {table_name} SET {column_name}=?', (value,))
            # Commit changes and close connection
            self.connection.commit()
            self.connection.close()
            return {'success': f'Column {column_name} added to table {table_name} and filled with value {value}'}
        except sqlite3.Error as e:
            return {'error': str(e)}

def write_order_to_csv(order: list[Seed_Product]):
    with open(order_file, 'w', newline='') as file:
        writer = csv.writer(file)
        for product in order:
            writer.writerow([product.id, product.amount, 'STK'])

@app.route('/', methods=['GET', 'POST'])
def order_form():
    database_service = Database_Service(seeds_db)
    if request.method == 'POST':
        order = []
        seeds_in_form = {seed: int(float(quantity)) for seed, quantity in request.form.to_dict().items() if quantity}
        ordered_seeds = {seed: quantity for seed, quantity in seeds_in_form.items() if quantity}
        for seed, quantity in ordered_seeds.items():
            name, pack_size = seed.rsplit('-', 1)
            code = database_service.get_code(name, pack_size)
            if not code: continue
            product = Seed_Product(name=name, pack_size=pack_size, id=code, amount=quantity)
            order.append(product)
        write_order_to_csv(order)
        for product in order:
            print(product)
    seed_names, pack_sizes, available_products = database_service.fetch_seed_data()
    return render_template('order_form.html', seed_names=seed_names, pack_sizes=pack_sizes, available_products=available_products)

@app.route('/download', methods=['GET', 'POST'])
def download():
    return send_file(
        path_or_file=order_file,
        mimetype='text/csv',
        download_name='Dutch_Passion_Order.csv',
        as_attachment=True,
        max_age=0)

@app.route('/get_seed', methods=['GET'])
def get_seed_route():
    database_service = Database_Service(seeds_db)
    database_service.connection.close()
    return database_service.get_seed()

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()