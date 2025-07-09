# SavoryBites

SavoryBites is a modern restaurant web application built with Django. It allows users to browse the menu, add items to a cart, place orders, make reservations, and pay online. The project is designed for both customers and restaurant staff, providing a seamless food ordering and management experience.

## Features

- User authentication (signup, login, logout)
- Menu browsing with categories (meals, drinks, desserts, etc.)
- Add to cart and cart management
- Checkout with delivery, takeaway, or dine-in options
- Online payment integration (Paystack)
- Order history and payment reports
- Reservation system
- Admin panel for menu and order management
- Responsive design for mobile and desktop

## Project Structure

```
savorybites/
├── core/                # Django project settings and core config
├── savorybites/         # Main Django app (models, views, templates, static)
│   ├── migrations/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
├── media/               # Uploaded images (menu, gallery, reviews)
├── db.sqlite3           # SQLite database (default)
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip
- (Optional) Virtualenv

### Installation
1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd savorybites
   ```
2. **Create and activate a virtual environment (recommended):**
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Mac/Linux
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up environment variables:**
   - Create a `.env` file in the root directory.
   - Add your Paystack keys and any other secrets:
     ```env
     PAYSTACK_PUBLIC_KEY=your_public_key
     PAYSTACK_SECRET_KEY=your_secret_key
     ```
5. **Apply migrations:**
   ```sh
   python manage.py migrate
   ```
6. **Create a superuser (for admin access):**
   ```sh
   python manage.py createsuperuser
   ```
7. **Run the development server:**
   ```sh
   python manage.py runserver
   ```
8. **Access the app:**
   - Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
   - Admin panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Usage
- Browse the menu and add items to your cart.
- Proceed to checkout, fill in your details, and place your order.
- Pay online using the integrated payment gateway.
- View your order and payment history in your profile.
- Make reservations for dine-in.

## Customization
- Update menu items, images, and categories via the Django admin panel.
- Edit templates in `savorybites/templates/` for UI changes.
- Static files (CSS, JS, images) are in `savorybites/static/`.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.

## Contact
For support or inquiries, please contact the project maintainer.
