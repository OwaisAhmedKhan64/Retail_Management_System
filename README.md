# Retail Management System
A retail management system which helps to reduce human errors by increasing data accountability and traceability. These both qualities help to get insights, which creates value (in business context: more market capture). 

This system is made in Python. GUI is made using the tkinter library and the database is made in SQLite.

Main Features of this system:
- It includes the POS (Point-of-Sale) system by which the sales in the business (shop) can be recorded.
- It automatically reduces the stock of a product after each sale, and records the revenue of each sale.
- Basic operations of adding, deleting, editing and restocking a product are available.
- Tracks customer purchase history and recency.
- It has RBAC (Role-Based Access Control). There are two types of users: admin (business owner) and cashier. The business owner has access to the entire software whereas the cashier has restricted access only for POS.
- The passwords for the users are hashed in the database using SHA-256 algorithm.
- The system is converted into an executable file so that it can work on any device running Windows 8 or above. It also does not need any dependencies.

Demo of the application: https://www.linkedin.com/posts/owaisahmedkhan64_%F0%9D%90%96%F0%9D%90%A1%F0%9D%90%B2-%F0%9D%90%9D%F0%9D%90%A8-%F0%9D%90%AC%F0%9D%90%A6%F0%9D%90%9A%F0%9D%90%A5%F0%9D%90%A5-%F0%9D%90%9B%F0%9D%90%AE%F0%9D%90%AC%F0%9D%90%A2%F0%9D%90%A7%F0%9D%90%9E%F0%9D%90%AC%F0%9D%90%AC%F0%9D%90%9E-activity-7412021604844707840-CSSE?utm_source=share&utm_medium=member_desktop&rcm=ACoAADgpsrsBUpBLi4xYr2fhsjUDHBqj3ENwbxI

How to run:

1. Go into releases.

2. Download 'retail_management_system.zip'.

3. Extract 'retail_management_system.zip'.

4. Run 'retail_management_system.exe'. If an antivirus marked the file as a threat, restore the file and run it.

5. Login with username 'admin1' and password '1234' for full access or, login with username 'cashier1' and password '5678' for restricted access.

Note: 

If you want to delete the existing records of customers and sales, delete 'retail_management_system.db' file. A new 'retail_management_system.db' file is automatically generated after running 'retail_management_system.exe'. The records of products and users remain the same.
