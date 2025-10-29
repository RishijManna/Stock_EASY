**DEPLOYMENT LINK ->** [Click Here](https://med-stock.onrender.com)
# 🩺 MedShop Tracker

> A full-stack **Django + Tailwind CSS** web app to manage a medical shop’s inventory, transactions, and analytics — built for speed, accuracy, and simplicity.

---

## 🚀 Features

- 🔐 **User Accounts** – Email login, profile page, Drug Selling Licence upload  
- 💊 **Medicine Inventory** – Add/Edit/Delete medicines, expiry tracking  
- 📦 **Transactions** – Record Bought/Sold, auto stock updates  
- 🏭 **Manufacturers** – Manage supplier details & search easily  
- 📊 **Reports Dashboard** – Plotly charts, profit/loss, expiry, revenue trends  
- 📤 **Export CSV** – Full data (not limited to last 15)  
- 💅 **Modern UI** – Tailwind, Inter font, dark/light mode, responsive navbar

---

## ⚙️ Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Django 5 / Python 3 |
| Frontend | Tailwind CSS + Plotly.js |
| Database | SQLite (default) |
| Auth | Django’s built-in system |
| Styling | Inter font + custom Tailwind theme |

---


## 📁 Project Structure

```
medshop-tracker/
│
├── accounts/           # Registration, login, profiles
├── inventory/          # Medicines, manufacturers, transactions
├── reports/            # Analytics & charts
│
├── templates/
│   ├── base.html
│   ├── navbar.html
│   └── ...pages...
│
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/        # Drug licence documents
│
├── db.sqlite3
└── manage.py
```

---

## 📊 Key Analytics

* Revenue (daily, weekly, monthly, yearly)
* Profit vs Loss (per medicine)
* Expiry status pie
* Bought vs Sold bar chart
* Rolling & cumulative revenue
* Sell-through % and Profit distribution
* All downloadable as CSVs

---


## 👨‍💻 Author

**RISHIJ MANNA**
💡 Django developer • Builder of MedShop Tracker
📬 Open to feedback and contributions!

---
**For making Any Changes**
```
git add .
git commit -m "Fixed navbar visibility on mobile and updated reports"
git push
```



