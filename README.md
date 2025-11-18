# Django E‑Commerce Project

A clean  **Django-based E-commerce application** built with:

* Django (Backend)
* Django Templates (Frontend UI)
* Django ORM (MySQL / SQLite / PostgreSQL)
* Django REST Framework (Cart, Wishlist, Products API)

This project includes:

* Product listing & detail pages
* Categories
* Cart & Wishlist
* Checkout workflow
* Address management
* Orders & order items
* Payment record model
---

##  Features

### **1. Products & Categories**

* Category model (name, slug, image)
* Product model (title, price, description, stock)
* Product images (multiple images per product)
* Product list & detail pages

### **2. User System**

* Addresses per user
* Default address handling

### **3. Cart**

* Add to cart
* Update quantity
* Remove items
* Auto subtotal calculation

### **4. Wishlist**

* Toggle wishlist
* Prevent duplicates

### **5. Orders & Checkout**

* Convert cart items → order items
* Stock reduction
* Total calculation
* Cart clears automatically

### **6. Payment Record**

* Payment ID
* Method
* Status
* Linked to order

### **7. Frontend Templates (Django)**

Includes:

* `base.html`
* `index.html`
* `product_detail.html`
* `cart.html`
* `wishlist.html`
* `checkout.html`

---


##  Installation & Setup

### **1. Clone project**

```
git clone 
cd ecommerce_project
```

### **2. Create virtual environment**

```
python -m venv venv
source venv/bin/activate     # Linux/Mac
venv\Scripts\activate        # Windows
```

### **3. Install dependencies**

```
pip install -r requirements.txt
```

### **4. Run migrations**

```
python manage.py makemigrations\python manage.py migrate
```

### **5. Create superuser**

```
python manage.py createsuperuser
```

### **6. Start server**

```
python manage.py runserver
```

---

## 🌐 URL Structure

### **Frontend (HTML)**

```
/
/product/<slug>/
/cart/
/wishlist/
/checkout/
```

### **API Endpoints (DRF)**

```
/api/products/
/api/products/<slug>/
/api/cart/add/
/api/cart/remove/
/api/wishlist/toggle/
/api/checkout/
```

---

##  Technologies Used

* Python 3
* Django
* Django REST Framework
* MySQL / SQLite / PostgreSQL
* HTML / CSS (Django Templates)

---

##  Notes

* This project uses separate URLs for **frontend** and **API**.
* Cart & Wishlist API require authentication.
* Templates are rendered directly for quick demo UI.


