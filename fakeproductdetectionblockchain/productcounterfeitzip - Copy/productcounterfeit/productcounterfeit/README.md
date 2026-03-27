# Product Counterfeit Detection System

This project is a web application designed to manage and verify product authenticity using blockchain technology. It allows manufacturers to register their products, vendors to manage inventory, and customers to verify product authenticity through QR codes.

## Features

- User authentication for different roles: Admin, Manufacturer, Vendor, and Customer.
- Product registration and management.
- Blockchain integration for product verification.
- QR code generation for each product.
- User-friendly dashboards for different roles.

## Project Structure

```
productcounterfeit
├── app3.py                # Main application logic using Flask
├── requirements.txt       # Project dependencies
├── .gitignore             # Files and directories to ignore in Git
├── templates              # HTML templates for the application
│   ├── base.html          # Base template for all pages
│   ├── login.html         # User login form
│   ├── register.html      # User registration form
│   ├── admin.html         # Admin dashboard
│   ├── manufacturer.html   # Manufacturer dashboard
│   ├── vendor.html        # Vendor dashboard
│   ├── customer.html      # Customer dashboard
│   ├── profile.html       # User profile page
│   └── errors             # Error templates
│       └── 404.html       # Custom 404 error page
├── static                 # Static files (CSS, JS, images)
│   ├── css
│   │   └── styles.css     # CSS styles for the application
│   ├── js
│   │   └── main.js        # JavaScript for client-side functionality
│   └── qrcodes            # Directory for storing generated QR codes
└── README.md              # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd productcounterfeit
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app3.py
   ```

4. Access the application in your web browser at `http://localhost:5000`.

## Usage

- Register as a new user or log in with existing credentials.
- Manufacturers can add products and generate QR codes.
- Vendors can view and purchase products.
- Customers can verify product authenticity using QR codes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.