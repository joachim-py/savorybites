import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from datetime import datetime

def send_email(subject, body_text, body_html, from_email, to_email):
    """Send an email with both plain text and HTML versions."""
    msg = EmailMultiAlternatives(subject, body_text, from_email, [to_email])
    msg.attach_alternative(body_html, "text/html")
    
    try:
        msg.send()
        print(f'Email sent to {to_email}!')
        return True
    except Exception as e:
        print(f'Failed to send email to {to_email}: {str(e)}')
        return False

def generate_receipt_pdf(order):
    """
    Generate a PDF receipt for the given order and save it to the media/receipts directory.
    Returns the path to the generated PDF file.
    """
    # Ensure the receipts directory exists
    receipt_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
    os.makedirs(receipt_dir, exist_ok=True)
    
    # Generate a filename using order number and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'receipt_{order.order_number}_{timestamp}.pdf'
    filepath = os.path.join(receipt_dir, filename)
    
    # Prepare context for the receipt template
    context = {
        'order': order,
        'order_items': order.orderitem_set.all(),
        'site_name': 'Savory Bites',
        'current_date': datetime.now().strftime('%B %d, %Y'),
    }
    
    # Render the receipt HTML
    html_string = render_to_string('emails/receipt_pdf.html', context)
    
    # Generate PDF using WeasyPrint
    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    html.write_pdf(target=filepath)
    
    # Return the relative path that can be used in URLs
    return os.path.join('receipts', filename)

def send_order_confirmation(order, receipt_path=None):
    """
    Send an order confirmation email to the customer with an optional receipt attachment.
    """
    subject = f'Order Confirmation - #{order.order_number}'
    
    # Plain text email body
    body_text = f"""
    Thank you for your order at Savory Bites!
    
    Order Number: {order.order_number}
    Order Date: {order.created_at.strftime('%B %d, %Y %H:%M')}
    Total Amount: ${order.total_amount:.2f}
    
    Your order is being processed and will be ready soon.
    
    Best regards,
    The Savory Bites Team
    """
    
    # HTML email body
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Order Confirmation - {order.order_number}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #000000;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
            }}
            .header {{
                background-color: #d4a76a;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                padding: 20px;
            }}
            .order-details {{
                margin: 20px 0;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            .footer {{
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #eeeeee;
                text-align: center;
                font-size: 12px;
                color: #777777;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Thank you for your order!</h1>
            </div>
            <div class="content">
                <p>Hello {order.user.get_full_name() or order.user.username},</p>
                <p>We've received your order and it's being processed. Here are your order details:</p>
                
                <div class="order-details">
                    <p><strong>Order Number:</strong> {order.order_number}</p>
                    <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y %H:%M')}</p>
                    <p><strong>Total Amount:</strong> ${order.total_amount:.2f}</p>
                </div>
                
                <p>You'll receive another email once your order is ready for {order.delivery_option}.</p>
                
                <p>If you have any questions about your order, please contact our support team.</p>
                
                <p>Best regards,<br>The Savory Bites Team</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} Savory Bites. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=body_text.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email]
    )
    
    # Attach HTML version
    email.attach_alternative(body_html, "text/html")
    
    # Attach receipt PDF if provided
    if receipt_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, receipt_path)):
        with open(os.path.join(settings.MEDIA_ROOT, receipt_path), 'rb') as pdf_file:
            email.attach(
                f'receipt_{order.order_number}.pdf',
                pdf_file.read(),
                'application/pdf'
            )
    
    # Send the email
    try:
        email.send()
        print(f'Order confirmation email sent to {order.user.email}')
        return True
    except Exception as e:
        print(f'Failed to send order confirmation email: {str(e)}')
        return False

def process_order_payment_confirmation(order):
    """
    Process an order after payment confirmation:
    1. Generate receipt PDF
    2. Send email with receipt
    3. Update order status if needed
    """
    try:
        # Generate and save the receipt
        receipt_path = generate_receipt_pdf(order)
        
        # Send the receipt email
        send_order_confirmation(order, receipt_path)
        
        return True
    except Exception as e:
        print(f'Error processing order confirmation: {str(e)}')
        return False
