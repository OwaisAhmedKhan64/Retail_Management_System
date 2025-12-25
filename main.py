import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import datetime


def get_connection():
    try:
        conn = sqlite3.connect("retail_management_system.db")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        print("Database Connection Successful")
        return conn
    except sqlite3.Error as e:
        print("Database connection failed:", e)
        return None

connection = get_connection()
cursor = connection.cursor()

def show_popup(options):
    global popup, listbox

    if popup is None:
        popup = tk.Toplevel(input_sale_tab)
        popup.wm_overrideredirect(True)

        listbox = tk.Listbox(popup, height=6, font=("Inter", 14))
        listbox.pack(fill="both", expand=True)
        listbox.bind("<<ListboxSelect>>", on_select)

    listbox.delete(0, tk.END)

    for opt in options:
        listbox.insert(tk.END, opt)

    x = select_products_entry.winfo_rootx()
    y = select_products_entry.winfo_rooty() + select_products_entry.winfo_height()

    popup.wm_geometry(f"+{x}+{y}")

def close_popup():
    global popup
    if popup:
        popup.destroy()
        popup = None

def on_key(event):
    text = select_products_entry.get().strip()

    if text == "":
        close_popup()
        return

    filtered = [item for item in products if text.lower() in item.lower()]

    if not filtered:
        close_popup()
        return

    show_popup(filtered)

def on_select(event):
    global listbox
    if listbox.curselection():
        selected = listbox.get(listbox.curselection())
        select_products_entry.delete(0, tk.END)
        select_products_entry.insert(0, selected)
    close_popup()

def update_grand_total():
    total = 0
    for record in sale_table.get_children():
        total_price = float(sale_table.item(record)['values'][3])
        total += total_price
    grand_total_value.set(f"{total:.0f}")

def confirm_product():
    try:
        product_name = select_products_entry.get().strip()
        quantity_bought = int(quantity_bought_entry.get().strip())

        if not product_name or not quantity_bought:
            messagebox.showerror("Error", "Product name and Quantity are required.")
            return

        cursor.execute("SELECT product_id, selling_price, product_quantity, cost_price FROM products WHERE product_name = ?",
            (product_name,))

        product = cursor.fetchone()
        if not product:
            messagebox.showerror("Error", "Product not found.")
            return
        if  quantity_bought > product["product_quantity"]:
            messagebox.showerror("Error", f"Not enough stock for '{product_name}'. Available: {product["product_quantity"]}")
            return

        total_price = product["selling_price"] * quantity_bought
        profit = (product["selling_price"] - product["cost_price"]) * quantity_bought
        sale_table.insert(
            "",
            "end",
            values=(product_name, quantity_bought, product['selling_price'], total_price)
        )
        update_grand_total()

        products_bought.append({
            "product_id": product['product_id'],
            "product_name": product_name,
            "selling_price": product['selling_price'],
            "quantity_bought": quantity_bought,
            "total_price": total_price,
            "profit": profit
        })

        select_products_entry.delete(0, "end")
        quantity_bought_entry.delete(0, "end")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to confirm product: {e}")

def confirm_sale():
    try:
        if not products_bought:
            messagebox.showerror("Error", "No products selected.")
            return

        customer_contact = customer_contact_entry.get().strip()

        sale_date = datetime.datetime.now()
        sale_date = sale_date.strftime("%d-%m-%Y %H:%M:%S")
        sale_revenue = 0
        sale_profit = 0

        cursor.execute("SELECT customer_id FROM customers WHERE customer_contact = ?",
                       (customer_contact,))
        result = cursor.fetchone()

        if result:
            customer_id = result['customer_id']
        else:
            cursor.execute("INSERT INTO customers (customer_contact) VALUES (?)",
                           (customer_contact,))
            connection.commit()
            customer_id = cursor.lastrowid

        for item in products_bought:
            sale_revenue += item["total_price"]
            sale_profit += item["profit"]

        cursor.execute(
            "INSERT INTO sales (customer_id, sale_date, sale_revenue, sale_profit) VALUES (?, ?, ?, ?)",
            (customer_id, sale_date, sale_revenue, sale_profit)
        )
        sale_id = cursor.lastrowid
        connection.commit()
        for item in products_bought:
            product_name = item["product_name"]
            quantity_bought = item["quantity_bought"]
            total_price = item['total_price']

            cursor.execute("SELECT product_id, selling_price, product_quantity, cost_price FROM products WHERE product_name = ?",
                (product_name,))
            product = cursor.fetchone()

            if not product:
                messagebox.showerror("Error", f"Product '{product_name}' not found.")
                return
            else:
                product_id = product['product_id']
                selling_price = float(product['selling_price'])
                cost_price = float(product['cost_price'])

            item_sale_total = total_price
            item_cost_total = cost_price * quantity_bought
            item_profit = item_sale_total - item_cost_total

            cursor.execute(
                """
                INSERT INTO sale_items 
                (sale_id, product_id, quantity_sold, selling_price_at_sale, cost_price_at_sale, item_sale_total, item_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sale_id, product_id, quantity_bought, selling_price, cost_price, item_sale_total, item_profit)
            )

            cursor.execute(
                "UPDATE products SET product_quantity = product_quantity - ? WHERE product_id = ?",
                (quantity_bought, product_id)
            )
            connection.commit()

        customer_contact_entry.delete(0, "end")
        for row in sale_table.get_children():
            sale_table.delete(row)
        products_bought.clear()
        refresh_products_table()
        refresh_customers_table()
        refresh_sales_table()
        grand_total_value.set("0")

        messagebox.showinfo("Sale Confirmed", f"Sale ID {sale_id} has been recorded successfully!")

    except Exception as e:
        connection.rollback()
        print("exception", e, type(e))
        messagebox.showerror("Error", f"Failed to confirm sale: {e}")

def refresh_products_table():
    for record in products_table.get_children():
        products_table.delete(record)
    cursor.execute("SELECT * FROM products WHERE is_deleted = 0")
    data = cursor.fetchall()
    for record in data:
        products_table.insert(
            "",
            "end",
            values=(record["product_id"], record["product_name"], record["product_quantity"], record["selling_price"],
                    record["cost_price"])
        )
def refresh_customers_table():
    for record in customers_table.get_children():
        customers_table.delete(record)

    # Fetch customer basic info
    cursor.execute("SELECT customer_id, customer_contact FROM customers ORDER BY customer_id ASC")
    customers = cursor.fetchall()

    for customer in customers:
        customer_id = customer["customer_id"]
        customer_contact = customer["customer_contact"]

        # Fetch last sale info for this customer
        cursor.execute("SELECT sale_revenue, sale_date FROM sales WHERE customer_id = ? ORDER BY sale_date DESC LIMIT 1",
                       (customer_id,))
        last_sale = cursor.fetchone()

        if last_sale:
            last_sale_amount = last_sale["sale_revenue"]
            last_sale_date = last_sale["sale_date"]
        else:
            last_sale_amount = ""
            last_sale_date = ""

        customers_table.insert(
            "",
            "end",
            values=(customer_id, customer_contact, last_sale_amount, last_sale_date)
        )

def refresh_sales_table():
    for record in sales_table.get_children():
        sales_table.delete(record)

    # Fetch all sales with customer contact
    cursor.execute("SELECT sales.sale_id, customers.customer_contact, sales.sale_date, sales.sale_revenue, sales.sale_profit FROM sales LEFT JOIN customers ON sales.customer_id = customers.customer_id ORDER BY sales.sale_date DESC")
    sales = cursor.fetchall()

    # Insert into the Treeview
    for sale in sales:
        sale_id = sale["sale_id"]
        customer_contact = sale["customer_contact"] if sale["customer_contact"] else ""
        sale_date = sale["sale_date"]
        sale_revenue = sale["sale_revenue"]
        sale_profit = sale["sale_profit"]

        sales_table.insert(
            "",
            "end",
            values=(sale_id, customer_contact, sale_date, sale_revenue, sale_profit)
        )

def search_product():
    selected_field = products_fields.get().strip()
    term = search_product_entry.get().strip()

    if not selected_field or not term:
        messagebox.showerror("Error", "Select a field and enter a search term")
        refresh_products_table()
        return

    field_mapping = {
        "Product ID": "product_id",
        "Product Name": "product_name",
        "Product Quantity": "product_quantity",
        "Product Price": "selling_price",
        "Cost Price": "cost_price"
    }

    field = field_mapping[selected_field]
    if field == "product_name":
        cursor.execute(f"SELECT * FROM products WHERE LOWER(product_name) LIKE ?",
                       (f"%{term.lower()}%",))
    else:
        cursor.execute(f"SELECT * FROM products WHERE {field} = ?", (term,))

    records = cursor.fetchall()
    # clear table
    for row in products_table.get_children():
        products_table.delete(row)

    # insert new rows
    for record in records:
        products_table.insert("", "end",
                              values=[record["product_id"], record["product_name"], record["product_quantity"], record["selling_price"], record["cost_price"]])

def add_new_product():
    # Create a popup window
    add_win = tk.Toplevel(master)
    add_win.title("Add Product")
    add_win.geometry("400x300")
    add_win.grab_set()  # Make modal

    # Labels and Entry fields
    ttk.Label(add_win, text="Product Name:", font = ("Inter", 14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    name_entry = ttk.Entry(add_win, font = ("Inter", 14))
    name_entry.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(add_win, text="Quantity:", font = ("Inter", 14)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    quantity_entry = ttk.Entry(add_win, font = ("Inter", 14))
    quantity_entry.grid(row=1, column=1, padx=10, pady=10)

    ttk.Label(add_win, text="Selling Price:", font = ("Inter", 14)).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    selling_price_entry = ttk.Entry(add_win, font = ("Inter", 14))
    selling_price_entry.grid(row=2, column=1, padx=10, pady=10)

    ttk.Label(add_win, text="Cost Price:", font = ("Inter", 14)).grid(row=3, column=0, padx=10, pady=10, sticky="w")
    cost_price_entry = ttk.Entry(add_win, font = ("Inter", 14))
    cost_price_entry.grid(row=3, column=1, padx=10, pady=10)

    def save_new_product():
        name = name_entry.get().strip()
        selling_price = selling_price_entry.get().strip()
        quantity = quantity_entry.get().strip()
        cost_price = cost_price_entry.get().strip()

        if not name or not selling_price or not quantity or not cost_price:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            selling_price = float(selling_price)
            quantity = int(quantity)
            cost_price = float(cost_price)
        except ValueError:
            messagebox.showerror("Error", "Invalid number format!")
            return

        try:
            cursor.execute(
                "INSERT INTO products (product_name, product_quantity, selling_price, cost_price) VALUES (?, ?, ?, ?)",
                (name, quantity, selling_price, cost_price)
            )
            connection.commit()
            refresh_products_table()
            messagebox.showinfo("Success", f"Product '{name}' added successfully!")
            add_win.destroy()  # Close popup

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    confirm_new_product_button = ttk.Button(add_win, text = "Confirm", style = "buttons.TButton", command = save_new_product)
    confirm_new_product_button.grid(row = 4, column = 1, pady = 30)

def delete_product():
    delete_win = tk.Toplevel(master)
    delete_win.title("Delete Product")
    delete_win.geometry("430x150")
    delete_win.focus_force()

    tk.Label(delete_win, text="Enter Product ID:", font = ("Inter", 14)).grid(row = 0, column = 0, padx = 10, pady = 10)
    product_id_entry = tk.Entry(delete_win, font = ("Inter", 14))
    product_id_entry.grid(row = 0, column = 1, padx = 10, pady = 10)

    def go_next():
        product_id = product_id_entry.get().strip()
        if not product_id.isdigit():
            messagebox.showerror("Error", "Invalid Product ID.")
            return

        cursor.execute("SELECT product_name FROM products WHERE product_id = ? AND is_deleted = 0" , (product_id,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Product not found.")
            delete_win.focus_force()
            return

        product_name = result["product_name"]

        # Confirmation message box
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f'Are you sure you want to delete "{product_name}" with ID "{product_id}"?'
        )

        if confirm:
            cursor.execute("UPDATE products SET is_deleted = 1 WHERE product_id = ?;", (product_id,))
            connection.commit()
            refresh_products_table()
            messagebox.showinfo("Success", "Product deleted successfully.")
            delete_win.destroy()

        else:
            delete_win.focus_force()

    next_button = ttk.Button(delete_win, text="Next", style = "buttons.TButton", command=go_next)
    next_button.grid(row = 1, column = 1, padx = 10, pady = 10)

def edit_product():
    # --- Tkinter Popup Window ---
    edit_window = tk.Toplevel()
    edit_window.title("Edit Product")
    edit_window.geometry("600x350")
    edit_window.grab_set()

    product_id = None

    ttk.Label(edit_window, text = "Enter Product ID:", font = ("Inter", 14)).grid(row = 0, column = 0, padx = 10, pady = 10)
    product_id_entry = tk.Entry(edit_window, font = ("Inter", 14))
    product_id_entry.grid(row = 0, column = 1, padx = 10, pady = 10)

    def fetch_product():
        nonlocal product_id
        product_id = product_id_entry.get().strip()
        if not product_id:
            messagebox.showerror("Error", "Please enter a Product ID")
            return

        # Fetch product details
        cursor.execute(
            "SELECT product_name, selling_price, cost_price, product_quantity FROM products WHERE product_id = ? AND is_deleted = 0",
            (product_id,))
        result = cursor.fetchone()
        if not result:
            messagebox.showerror("Error", "Product not found or deleted")
            return

        # Populate fields
        name_var.set(result["product_name"])
        selling_price_var.set(result["selling_price"])
        cost_price_var.set(result["cost_price"])
        quantity_var.set(result["product_quantity"])

        fetch_btn.config(state="disabled")  # Disable fetch after fetching

    fetch_btn = ttk.Button(edit_window, text = "Fetch Product", style = "buttons.TButton", command = fetch_product)
    fetch_btn.grid(row = 0, column = 2, padx = 10, pady = 10)

    name_var = tk.StringVar()
    selling_price_var = tk.StringVar()
    cost_price_var = tk.StringVar()
    quantity_var = tk.StringVar()

    ttk.Label(edit_window, text="Product Name:", font = ("Inter", 14)).grid(row = 1, column = 0, padx = 10, pady = 10)
    ttk.Entry(edit_window, textvariable=name_var, font = ("Inter", 14)).grid(row = 1, column = 1, padx = 10, pady = 10)

    ttk.Label(edit_window, text="Selling Price:", font = ("Inter", 14)).grid(row = 2, column = 0, padx = 10, pady = 10)
    ttk.Entry(edit_window, textvariable=selling_price_var, font = ("Inter", 14)).grid(row = 2, column = 1, padx = 10, pady = 10)

    ttk.Label(edit_window, text="Cost Price:", font = ("Inter", 14)).grid(row = 3, column = 0, padx = 10, pady = 10)
    ttk.Entry(edit_window, textvariable=cost_price_var, font = ("Inter", 14)).grid(row = 3, column = 1, padx = 10, pady = 10)

    def update_product():
        name = name_var.get().strip()
        try:
            selling_price = float(selling_price_var.get())
            cost_price = float(cost_price_var.get())
        except ValueError:
            messagebox.showerror("Error", "Price must be a number and quantity must be an integer")
            return

        if not name:
            messagebox.showerror("Error", "Product name and category cannot be empty")
            return

        if selling_price < 0 or cost_price < 0:
            messagebox.showerror("Error", "Values cannot be negative")
            return

        if messagebox.askyesno("Confirm Update", f"Are you sure you want to update Product ID {product_id}?"):
            try:
                cursor.execute("UPDATE products SET product_name = ?, selling_price = ?, cost_price = ? WHERE product_id = ?",
                               (name, selling_price, cost_price, product_id))
                connection.commit()
                refresh_products_table()
                messagebox.showinfo("Success", "Product updated successfully")
                edit_window.destroy()
            except Exception as e:
                connection.rollback()
                messagebox.showerror("Error", f"Failed to update product.\n{str(e)}")

    ttk.Button(edit_window, text="Update Product", style = "buttons.TButton", command = update_product).grid(row = 4, column = 1, padx = 10, pady = 10)

def restock_product():
    restock_win = tk.Toplevel(master)
    restock_win.title("Restock Product")
    restock_win.geometry("500x240")
    restock_win.grab_set()  # keep popup on top
    restock_win.focus_force()

    ttk.Label(restock_win, text="Product ID:", font = ("Inter", 14)).grid(row = 0, column = 0, padx = 10, pady = 10)
    product_id_entry = ttk.Entry(restock_win, font = ("Inter", 14))
    product_id_entry.grid(row = 0, column = 1, padx = 10, pady = 10)

    ttk.Label(restock_win, text="Quantity Added:", font = ("Inter", 14)).grid(row = 1, column = 0, padx = 10, pady = 10)
    quantity_added_entry = ttk.Entry(restock_win, font = ("Inter", 14))
    quantity_added_entry.grid(row = 1, column = 1, padx = 10, pady = 10)

    ttk.Label(restock_win, text="Cost Price at Restock:", font = ("Inter", 14)).grid(row = 2, column = 0, padx = 10, pady = 10)
    cost_price_entry = ttk.Entry(restock_win, font = ("Inter", 14))
    cost_price_entry.grid(row = 2, column = 1, padx = 10, pady = 10)

    def process_restock():
        product_id = product_id_entry.get().strip()
        quantity_added = quantity_added_entry.get().strip()
        cost_price = cost_price_entry.get().strip()

        if not product_id or not quantity_added or not cost_price:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            product_id = int(product_id)
            quantity_added = int(quantity_added)
            cost_price = float(cost_price)
        except TypeError:
            messagebox.showerror("Error", "Invalid data type.")
            return

        cursor.execute("SELECT product_name FROM products WHERE product_id = ?",
                       (product_id,))
        product_name = cursor.fetchone()
        if not product_name:
            messagebox.showerror("Error", "Invalid Product ID")
            return
        else:
            product_name = product_name["product_name"]

        confirm = messagebox.askyesno("Confirm",
                                      f"Are you sure you want to restock?\n"
                                      f"Product ID: {product_id}\n"
                                      f"Product Name: {product_name}\n"
                                      f"Quantity: {quantity_added}\n"
                                      f"Cost Price: {cost_price}")

        if confirm:
            # update products table
            cursor.execute("UPDATE products SET product_quantity = product_quantity + ? WHERE product_id = ?",
                           (quantity_added, product_id))

            time = datetime.datetime.now()
            # insert into restock table
            cursor.execute("INSERT INTO restocks (product_id, quantity_added, cost_price_at_restock, restock_date) VALUES (?, ?, ?, ?)",
                           (product_id, quantity_added, cost_price, time))
            connection.commit()

            refresh_products_table()
            messagebox.showinfo("Success", "Restock completed.")
            restock_win.destroy()

        else:
            restock_win.deiconify()
            restock_win.lift()
            restock_win.focus_force()

    ttk.Button(restock_win, text="Next", style = "buttons.TButton",
               command=process_restock).grid(row = 3, column = 1, padx = 10, pady=20)

def open_login_window():
    master.withdraw()

    login_window = tk.Toplevel()
    login_window.title("Login")
    login_window.geometry("480x490")

    ttk.Label(login_window, text="Welcome to Retail Management System", font=("Inter", 18, "bold")).grid(row=0, column=0, columnspan=2, padx = 10, pady= 10)

    ttk.Label(login_window, text = "Powered by:", font = ("Inter", 16, "bold")).grid(row=1, column=0, padx = (40,0), pady= (30,100))
    logo_image = tk.PhotoImage(file="oak_solutions_logo.png")
    small_logo = logo_image.subsample(2,2)
    login_window.small_logo = small_logo
    ttk.Label(login_window, image=small_logo).grid(row=1, column=1, pady=(30,100))

    ttk.Label(login_window, text="Username", font = ("Inter", 14)).grid(row = 2, column = 0, padx = 10, pady = 10)
    user_entry = ttk.Entry(login_window, font = ("Inter", 14))
    user_entry.grid(row = 2, column = 1, padx = 10, pady = 10)

    ttk.Label(login_window, text="Password", font = ("Inter", 14)).grid(row = 3, column = 0, padx = 10, pady = 10)
    pass_entry = ttk.Entry(login_window, show="*", font = ("Inter", 14))
    pass_entry.grid(row = 3, column = 1, padx = 10, pady = 10)

    def login():
        username = user_entry.get()
        password = pass_entry.get()
        query = "SELECT role FROM users WHERE username=? AND password=?"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        if result:
            user_role = result["role"]
            if user_role == "cashier":
                tabs.hide(products_tab)
                tabs.hide(customers_tab)
                tabs.hide(sales_tab)
            else:
                tabs.add(products_tab)
                tabs.add(customers_tab)
                tabs.add(sales_tab)

            login_window.destroy()
            master.state("zoomed")
        else:
            messagebox.showerror("Error", "Invalid username or password")

    ttk.Button(login_window, text="Login", style = "buttons.TButton", command = login).grid(row = 4, column = 1, padx = 10, pady = 10)
    login_window.protocol("WM_DELETE_WINDOW", lambda: master.destroy())

def logout():
    answer = messagebox.askyesno("Logout", "Are you sure you want to logout?")
    if answer:
        open_login_window()
    else:
        return

def load_logo(tab):
    logo_frame = ttk.Frame(tab)
    logo_frame.place(x=0, y=550, width="600", height="200")

    ttk.Label(logo_frame, text="Powered by:", font=("Inter", 15)).grid(row=0, column=0, padx=0, pady=10)

    logo_image = tk.PhotoImage(file="oak_solutions_logo.png")
    small_logo = logo_image.subsample(3, 3)
    tab.small_logo = small_logo
    ttk.Label(logo_frame, image=small_logo).grid(row=0, column=1, padx=0, pady=0)

'''=========================GRAPHICAL USER INTERFACE========================='''

master = tk.Tk()
master.title("Retail Management System")
master.geometry()
master.state("zoomed")

role = None

open_login_window()

tabs = ttk.Notebook(master, style="tabs.TNotebook")  # Make tabs
tabs.pack(fill="both", expand=True)  # fill in both directions and move correctly while resizing window.

input_sale_tab = ttk.Frame(tabs)
products_tab = ttk.Frame(tabs)
customers_tab = ttk.Frame(tabs)
sales_tab = ttk.Frame(tabs)
profile_tab = ttk.Frame(tabs)

tabs.add(input_sale_tab, text="   Input Sale   ")
tabs.add(products_tab, text="     Products    ")
tabs.add(customers_tab, text="    Customers    ")
tabs.add(sales_tab, text="      Sales     ")
tabs.add(profile_tab, text="     Profile     ")

# Making styles
style = ttk.Style()
style.configure("tabs.TNotebook.Tab", font = ("Inter", 20))
style.configure("labels.TLabel", font = ("Inter", 16))
style.configure("grand_total_label.TLabel", font = ("Inter", 20, "bold"), foreground = "white", background = "#3498DB")
style.configure("entries.TEntry", font = ("Inter", 16))
style.configure("buttons.TButton", font = ("Inter", 16))
style.configure("sale_input_frame.TFrame", font = ("Inter", 16), background = "light grey")
style.configure("sale_table_frame.TFrame", font = ("Inter", 16), background = "white")
style.configure("sale_result_frame.TFrame", font = ("Inter", 16), background = "#3498DB")
style.configure("sale_table.Treeview", font = ("Inter", 14), rowheight = 30)
style.configure("sale_table.Treeview.Heading", font = ("Inter", 18))
style.configure("products_table.Treeview", font = ("Inter", 14), rowheight = 30)
style.configure("products_table.Treeview.Heading", font = ("Inter", 16))

cursor.execute("SELECT product_name FROM products WHERE is_deleted = 0")
rows = cursor.fetchall()
products = [row["product_name"] for row in rows]

'''=========================INPUT SALE TAB========================='''

products_bought = []
popup = None
listbox = None

grand_total_value = tk.StringVar()
grand_total_value.set("0")

sale_input_frame = ttk.Frame(input_sale_tab, style = "sale_input_frame.TFrame")
sale_input_frame.place(x = 0, y = 150, width = "760", height = "300")
sale_input_frame.grid_rowconfigure(1, minsize = 40)

ttk.Label(sale_input_frame, text = "Customer Contact", style = "labels.TLabel").grid(row = 0, column = 0, padx = 5, pady = 5)
ttk.Label(sale_input_frame, text = "Select Products", style = "labels.TLabel").grid(row = 2, column = 0, padx = 5, pady = 5)
ttk.Label(sale_input_frame,text = "Quantity", style = "labels.TLabel").grid(row = 2, column = 2, padx = 5, pady = 5)

customer_contact_entry = ttk.Entry(sale_input_frame, font=("Inter", 14))
customer_contact_entry.grid(row = 0, column = 1, padx = 5, pady = 5)
select_products_entry = ttk.Entry(sale_input_frame, font=("Inter", 14))
select_products_entry.grid(row = 2, column = 1, padx = 5, pady = 5)
select_products_entry.bind("<KeyRelease>", on_key)
quantity_bought_entry = ttk.Entry(sale_input_frame, font=("Inter", 14))
quantity_bought_entry.grid(row = 2, column = 3, padx = 5, pady = 5)

ttk.Button(sale_input_frame, text = "Confirm Product", style = "buttons.TButton", command = confirm_product).grid(row = 3, column = 3, padx = 5, pady = 5)

sale_result_frame = ttk.Frame(input_sale_tab, style = "sale_result_frame.TFrame")
sale_result_frame.place(x = 766, y  = 570, width = "600", height = "80")

ttk.Label(sale_result_frame, text = "Grand Total:", style = "grand_total_label.TLabel").pack(side = "left", anchor = "w", padx = 10)
ttk.Label(sale_result_frame, textvariable = grand_total_value, style = "grand_total_label.TLabel").pack(side= "left", anchor = "w")

ttk.Button(sale_result_frame, text = "Finish Sale", style = "buttons.TButton", command = confirm_sale).pack(side = "right", anchor = "e", padx = 10, pady = 5)

sale_table_frame = ttk.Frame(input_sale_tab, style = "sale_table_frame.TFrame")
sale_table_frame.place(x = 766, y  = 0, width = "600", height = "570")

sale_table = ttk.Treeview(sale_table_frame,
                                     columns = ("product_name", "quantity_bought", "price_per_unit", "total_price"),
                                     show = "headings",
                                     height = 10,
                                     style = "sale_table.Treeview")
sale_table.heading("product_name", text = "Product Name")
sale_table.heading("quantity_bought", text = "Qty")
sale_table.heading("price_per_unit", text = "Price")
sale_table.heading("total_price", text = "Total Price")
sale_table.column("product_name", width = 290)
sale_table.column("quantity_bought", width = 65)
sale_table.column("price_per_unit", width = 110)
sale_table.column("total_price", width = 135)
sale_table.pack(fill = "both", expand = True)

load_logo(input_sale_tab)

'''=========================PRODUCTS TAB========================='''

search_product_frame = ttk.Frame(products_tab, style = "sale_input_frame.TFrame")
search_product_frame.place(x = 10, y = 150, width = "580", height = "100")

ttk.Label(search_product_frame, text = "Search Product", style = "labels.TLabel").grid(row = 0, column = 0, padx = 5, pady = 10)
search_product_entry = ttk.Entry(search_product_frame, font = ("Inter", 14))
search_product_entry.grid(row = 0, column = 1, padx = 5, pady = 10)
ttk.Label(search_product_frame, text = "by", style = "labels.TLabel").grid(row = 1, column = 0, padx = 2, pady = 10)
products_fields = ttk.Combobox(search_product_frame,
                               values = ["Product ID", "Product Name", "Product Quantity", "Product Price", "Cost Price"],
                               font = ("Inter", 14))
products_fields.grid(row = 1, column = 1, padx = 5, pady = 10)
ttk.Button(search_product_frame, text = "Search", style = "buttons.TButton",
           command = search_product).grid(row = 1, column = 3, padx = 5, pady = 10)

products_buttons_frame = ttk.Frame(products_tab, style = "sale_input_frame.TFrame")
products_buttons_frame.place(x = 60, y = 280, width = "410", height = "150")

ttk.Button(products_buttons_frame, text = "Add New Product", style = "buttons.TButton",
           command = add_new_product).grid(row = 0, column = 0, padx = 20, pady = 20)
ttk.Button(products_buttons_frame, text = "Delete Product", style = "buttons.TButton",
           command = delete_product).grid(row = 0, column = 1, padx = 5, pady = 10)
ttk.Button(products_buttons_frame, text = "Edit Product", style = "buttons.TButton",
           command = edit_product).grid(row = 1, column = 0, padx = 5, pady = 10)
ttk.Button(products_buttons_frame, text = "Restock Product", style = "buttons.TButton",
           command = restock_product).grid(row = 1, column = 1, padx = 5, pady = 10)

products_name_frame = ttk.Frame(products_tab)
products_name_frame.place(x = 600, y = 0, width = "760", height = "30")
ttk.Label(products_name_frame, text = "Products", style = "labels.TLabel").grid(row = 0, column = 0, padx = 350, pady = 0)

products_table_frame = ttk.Frame(products_tab, style = "sale_input_frame.TFrame")
products_table_frame.place(x = 600, y = 30, width = "760", height = "624")

products_table = ttk.Treeview(products_table_frame,
                                     columns = ("product_id", "product_name", "product_quantity", "selling_price", "cost_price"),
                                     show = "headings",
                                     height = 10,
                                     style = "products_table.Treeview")
products_table.heading("product_id", text = "ID")
products_table.heading("product_name", text = "Name")
products_table.heading("product_quantity", text = "Qty")
products_table.heading("selling_price", text = "Unit Selling Price")
products_table.heading("cost_price", text = "Unit Cost Price")
products_table.column("product_id", width = 56)
products_table.column("product_name", width = 266)
products_table.column("product_quantity", width = 70)
products_table.column("selling_price", width = 184)
products_table.column("cost_price", width = 172)
products_table.pack(side="left", fill = "both", expand = True)

products_scroll = ttk.Scrollbar(
    products_table_frame,
    orient="vertical",
    command=products_table.yview
)
products_scroll.pack(side = "right", fill = "y")
products_table.configure(yscrollcommand = products_scroll.set)

refresh_products_table()

load_logo(products_tab)

'''=========================CUSTOMERS TAB========================='''

customers_name_frame = ttk.Frame(customers_tab)
customers_name_frame.place(x = 600, y = 0, width = "760", height = "30")
ttk.Label(customers_name_frame, text = "Customers", style = "labels.TLabel").grid(row = 0, column = 0, padx = 350, pady = 0)

customers_table_frame = ttk.Frame(customers_tab, style = "sale_input_frame.TFrame")
customers_table_frame.place(x = 600, y = 30, width = "760", height = "624")

customers_table = ttk.Treeview(customers_table_frame,
                                     columns = ("customer_id", "customer_contact", "last_sale", "last_sale_date"),
                                     show = "headings",
                                     height = 10,
                                     style = "products_table.Treeview")
customers_table.heading("customer_id", text = "ID")
customers_table.heading("customer_contact", text = "Contact")
customers_table.heading("last_sale", text = "Last Sale")
customers_table.heading("last_sale_date", text = "Last Sale Date")
customers_table.column("customer_id", width = 46)
customers_table.column("customer_contact", width = 226)
customers_table.column("last_sale", width = 100)
customers_table.column("last_sale_date", width = 204)

customers_table.pack(side="left", fill = "both", expand = True)

customers_scroll = ttk.Scrollbar(
    customers_table_frame,
    orient = "vertical",
    command = customers_table.yview
)
customers_scroll.pack(side = "right", fill = "y")
customers_table.configure(yscrollcommand = customers_scroll.set)

refresh_customers_table()

load_logo(customers_tab)

'''=========================SALES TAB========================='''

sales_name_frame = ttk.Frame(sales_tab)
sales_name_frame.place(x = 600, y = 0, width = "760", height = "30")
ttk.Label(sales_name_frame, text = "Sales", style = "labels.TLabel").grid(row = 0, column = 0, padx = 350, pady = 0)

sales_table_frame = ttk.Frame(sales_tab, style = "sale_input_frame.TFrame")
sales_table_frame.place(x = 600, y = 30, width = "760", height = "624")

sales_table = ttk.Treeview(sales_table_frame,
                                     columns = ("sale_id", "customer_contact", "sale_date", "sale_revenue", "sale_profit"),
                                     show = "headings",
                                     height = 10,
                                     style = "products_table.Treeview")
sales_table.heading("sale_id", text = "ID")
sales_table.heading("customer_contact", text = "Customer Contact")
sales_table.heading("sale_date", text = "Sale Date")
sales_table.heading("sale_revenue", text = "Sale Revenue")
sales_table.heading("sale_profit", text = "Sale Profit")
sales_table.column("sale_id", width = 46)
sales_table.column("customer_contact", width = 186)
sales_table.column("sale_date", width = 200)
sales_table.column("sale_revenue", width = 142)
sales_table.column("sale_profit", width = 142)

sales_table.pack(side="left", fill = "both", expand = True)

sales_scroll = ttk.Scrollbar(
    sales_table_frame,
    orient = "vertical",
    command = sales_table.yview
)
sales_scroll.pack(side = "right", fill = "y")
sales_table.configure(yscrollcommand = sales_scroll.set)

refresh_sales_table()

load_logo(sales_tab)

'''=========================PROFILE TAB========================='''

logout_button = ttk.Button(profile_tab, text = "Logout", style = "buttons.TButton",
                                 command = logout)
logout_button.grid(row = 1, column = 0, padx = 5, pady = 40)

load_logo(profile_tab)

master.mainloop()