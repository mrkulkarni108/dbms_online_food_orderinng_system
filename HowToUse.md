# How to Install and Use Online Food Delivery System

This guide explains how to install, set up, and run the Online Food Delivery System on your local computer.

The project is built using Flask for the backend, MySQL for the database, and HTML, CSS, and JavaScript for the frontend.

---

## 1. Requirements

Before starting, make sure you have the following software installed on your system:

* Python 3.10 or above
* MySQL Server
* MySQL Workbench
* Visual Studio Code
* Git
* Web browser such as Google Chrome or Microsoft Edge

---

## 2. Download or Clone the Project

Open Git Bash, Command Prompt, or PowerShell and run the following command:

```bash
git clone https://github.com/your-username/online-food-delivery-system.git
```

After cloning, open the project folder:

```bash
cd online-food-delivery-system
```

If you downloaded the project as a ZIP file, extract it first and then open the extracted folder in VS Code.

---

## 3. Open the Project in VS Code

Open Visual Studio Code and select:

```text
File > Open Folder
```

Then choose the project folder:

```text
online-food-delivery-system
```

You can also open it directly from terminal:

```bash
code .
```

---

## 4. Create a Virtual Environment

A virtual environment keeps the project dependencies separate from your system Python.

### For Windows

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
.venv\Scripts\activate
```

If PowerShell blocks activation, run this command:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.venv\Scripts\activate
```

### For Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, you should see `(.venv)` at the beginning of your terminal line.

---

## 5. Install Required Python Packages

Install Flask and MySQL connector:

```bash
pip install flask mysql-connector-python
```

If the project contains a `requirements.txt` file, use this instead:

```bash
pip install -r requirements.txt
```

To verify Flask is installed:

```bash
python -m flask --version
```

---

## 6. Start MySQL Server

Make sure MySQL Server is running on your system.

You can check it from:

```text
Services > MySQL
```

or open MySQL Workbench and connect to your local MySQL server.

Use your MySQL username and password. In most local systems, the username is:

```text
root
```

---

## 7. Create the Database

Open MySQL Workbench and run the following SQL command:

```sql
CREATE DATABASE online_food_delivery;
```

Then select the database:

```sql
USE online_food_delivery;
```

---

## 8. Import the Database File

If the project contains a database file such as:

```text
database/database.sql
```

import it into MySQL.

### Method 1: Using MySQL Workbench

1. Open MySQL Workbench.
2. Connect to your local MySQL server.
3. Open the `database.sql` file.
4. Select the database:

```sql
USE online_food_delivery;
```

5. Run the full SQL script.

### Method 2: Using Command Prompt or Git Bash

```bash
mysql -u root -p online_food_delivery < database/database.sql
```

After running this command, enter your MySQL password.

### Method 3: Using Windows PowerShell

PowerShell does not support `<` redirection in the same way as Command Prompt, so use this command:

```powershell
Get-Content .\database\database.sql | mysql -u root -p online_food_delivery
```

If `mysql` is not recognized, use the full MySQL path:

```powershell
Get-Content .\database\database.sql | & "C:\Program Files\MySQL\MySQL Server 9.5\bin\mysql.exe" -u root -p online_food_delivery
```

Enter your MySQL password when asked.

---

## 9. Check Database Tables

After importing the SQL file, check whether the tables are created properly.

Run this in MySQL Workbench:

```sql
USE online_food_delivery;
SHOW TABLES;
```

Expected tables may include:

```text
users
restaurants
food_items
orders
products
order_products
payment
```

To check table data:

```sql
SELECT * FROM users;
SELECT * FROM restaurants;
SELECT * FROM food_items;
```

---

## 10. Configure Database Connection in Flask

Open the main Flask file. It may be located at:

```text
app.py
```

or:

```text
backend/app.py
```

Find the MySQL connection code and update it according to your system.

Example:

```python
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_mysql_password",
    database="online_food_delivery"
)
```

Replace:

```text
your_mysql_password
```

with your actual MySQL password.

Make sure the database name is exactly the same as the database created in MySQL:

```text
online_food_delivery
```

---

## 11. Run the Flask Application

If `app.py` is in the main project folder, run:

```bash
python app.py
```

If `app.py` is inside the `backend` folder, run:

```bash
python backend/app.py
```

If everything is correct, Flask will start and show something like:

```text
Running on http://127.0.0.1:5000/
```

---

## 12. Open the Project in Browser

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

or:

```text
http://localhost:5000/
```

Now the Online Food Delivery System should open in your browser.

---

## 13. How to Use the Application

### Step 1: Register

Create a new user account by entering your details such as name, email, password, address, and city.

### Step 2: Login

Log in using your registered email and password.

### Step 3: Browse Restaurants

After login, view the list of available restaurants.

### Step 4: View Menu

Select a restaurant and check the available food items with their prices.

### Step 5: Add Items to Cart

Choose food items and add them to your cart.

### Step 6: Check Total Amount

The system calculates the total price of selected food items.

### Step 7: Place Order

Confirm the cart and place your order.

### Step 8: Order Confirmation

After placing the order, the system displays an order confirmation message.

---

## 14. Common Errors and Solutions

### Error 1: `python is not recognized`

Python is not added to PATH.

Solution:

* Reinstall Python.
* During installation, tick `Add Python to PATH`.
* Restart VS Code or terminal.

Check Python version:

```bash
python --version
```

---

### Error 2: `flask is not recognized` or `No module named flask`

Flask is not installed in the active environment.

Solution:

```bash
pip install flask
```

If using virtual environment, activate it first:

```bash
.venv\Scripts\activate
```

Then install Flask again.

---

### Error 3: `No module named mysql.connector`

MySQL connector is missing.

Solution:

```bash
pip install mysql-connector-python
```

---

### Error 4: MySQL connection failed

Possible reasons:

* MySQL server is not running
* Wrong username
* Wrong password
* Wrong database name
* Database not created

Solution:

Check your MySQL connection details in `app.py`:

```python
host="localhost"
user="root"
password="your_mysql_password"
database="online_food_delivery"
```

Also check that the database exists:

```sql
SHOW DATABASES;
```

---

### Error 5: `mysql is not recognized`

MySQL is not added to PATH.

Solution for Windows PowerShell:

```powershell
& "C:\Program Files\MySQL\MySQL Server 9.5\bin\mysql.exe" -u root -p
```

If your MySQL version is different, change the folder name accordingly.

---

### Error 6: PowerShell database import not working with `<`

PowerShell does not support this command properly:

```powershell
mysql -u root -p online_food_delivery < database/database.sql
```

Use this instead:

```powershell
Get-Content .\database\database.sql | mysql -u root -p online_food_delivery
```

or with full MySQL path:

```powershell
Get-Content .\database\database.sql | & "C:\Program Files\MySQL\MySQL Server 9.5\bin\mysql.exe" -u root -p online_food_delivery
```

---

### Error 7: Port 5000 already in use

Another application is already using port 5000.

Solution:

Change the Flask port in `app.py`:

```python
if __name__ == "__main__":
    app.run(debug=True, port=5001)
```

Then open:

```text
http://127.0.0.1:5001/
```

---

### Error 8: Templates not found

Flask cannot find HTML files.

Solution:

Make sure your HTML files are inside a folder named:

```text
templates
```

Correct structure:

```text
project-folder/
│
├── app.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── menu.html
│   └── cart.html
```

---

### Error 9: Static files not loading

CSS, JavaScript, or images are not loading.

Solution:

Make sure static files are inside the `static` folder.

Correct structure:

```text
project-folder/
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── images/
```

In HTML, use Flask's `url_for` method:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
```

---

## 15. Recommended Project Structure

```text
online-food-delivery-system/
│
├── app.py
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── menu.html
│   ├── cart.html
│   └── order_success.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── images/
│
├── database/
│   └── database.sql
│
├── README.md
├── HOW_TO_USE.md
└── requirements.txt
```

If your project uses a `backend` folder, the structure may look like this:

```text
online-food-delivery-system/
│
├── backend/
│   └── app.py
│
├── templates/
├── static/
├── database/
├── README.md
└── HOW_TO_USE.md
```

---

## 16. Creating a `requirements.txt` File

To make installation easier for others, create a `requirements.txt` file.

Run this command after installing all packages:

```bash
pip freeze > requirements.txt
```

Then other users can install all dependencies using:

```bash
pip install -r requirements.txt
```

For this project, the minimum requirements are usually:

```text
Flask
mysql-connector-python
```

---

## 17. GitHub Upload Commands

After adding or updating files, use these commands:

```bash
git status
```

Add all changed files:

```bash
git add .
```

Commit changes:

```bash
git commit -m "Add installation and usage guide"
```

Push to GitHub:

```bash
git push
```

If pushing for the first time:

```bash
git branch -M main
git push -u origin main
```

---

## 18. Important Notes

* Keep MySQL Server running while using the project.
* The database name in Flask must match the database name in MySQL.
* Import the SQL file before running the Flask application.
* Do not delete required tables after importing the database.
* Use the correct MySQL username and password.
* Activate the virtual environment before running the project.
* Run the project from the correct folder location.

---

## 19. Final Usage Summary

The Online Food Delivery System allows users to register, log in, browse restaurants, view menus, add food items to the cart, and place orders.

This project is useful for understanding how a database-driven web application works. It shows the connection between frontend pages, Flask backend logic, and MySQL database operations in a simple and practical way.
