import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from xhtml2pdf import pisa
from datetime import datetime
from email.utils import formataddr

def generate_receipt_pdf(order):
    """
    Generate a PDF receipt for the given order.
    Returns the path to the generated PDF file or None if generation fails.
    """
    try:
        # In production, we might want to use a different storage backend
        if settings.DEBUG:
            # In development, save to local filesystem
            receipt_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
            os.makedirs(receipt_dir, exist_ok=True)
            
            # Generate a filename using order number and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'receipt_{order.order_id}_{timestamp}.pdf'
            filepath = os.path.join(receipt_dir, filename)
            
            # Prepare context for the receipt template
            context = {
                'order': order,
                'order_items': order.order_items.all(),
                'site_name': 'Savory Bites Restaurant',
                'current_date': datetime.now().strftime('%B %d, %Y'),
            }
            
            # Render the receipt HTML
            html_string = render_to_string('emails/receipt_pdf.html', context)

            # Generate PDF using xhtml2pdf
            with open(filepath, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)
                
                if pisa_status.err:
                    print(f'Error generating PDF: {pisa_status.err}')
                    return None
            
            # Return the relative path that can be used in URLs
            return os.path.join('receipts', filename)
        else:
            # In production, we'll generate the PDF in memory and return it directly
            # This avoids filesystem issues on platforms like Render
            from io import BytesIO
            
            # Prepare context for the receipt template
            context = {
                'order': order,
                'order_items': order.order_items.all(),
                'site_name': 'Savory Bites Restaurant',
                'current_date': datetime.now().strftime('%B %d, %Y'),
            }
            
            # Render the receipt HTML
            html_string = render_to_string('emails/receipt_pdf.html', context)
            
            # Create a BytesIO buffer to receive PDF data
            pdf_buffer = BytesIO()
            
            # Generate PDF using xhtml2pdf
            pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
            
            if pisa_status.err:
                print(f'Error generating PDF: {pisa_status.err}')
                return None
                
            # Reset buffer position to the beginning
            pdf_buffer.seek(0)
            return pdf_buffer
            
    except Exception as e:
        print(f'Error in generate_receipt_pdf: {str(e)}')
        return None

def send_order_confirmation(order, receipt=None, is_file_object=False):
    """
    Send an order confirmation email to the customer with an optional receipt attachment.
    
    Args:
        order: The order object
        receipt: Either a file path (str) or a file-like object containing the PDF
        is_file_object: If True, receipt is treated as a file-like object instead of a path
    """
    try:
        subject = f'Order Confirmation - #{order.order_id}'

        # Plain text email body
        body_text = f"""
        Thank you for your order at Savory Bites!

        Order Number: {order.order_id}
        Order Date: {order.order_date.strftime('%B %d, %Y %H:%M')}
        Total Amount: ₦{order.delivery_price:.2f}
        
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
            <title>Order Confirmation - {order.order_id}</title>
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
                    background-color: darkorange;
                    color: #000;
                    padding: 10px;
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
                    <h1>Savory Bites Restaurant</h1>
                </div>
                <div class="content">
                    <p>Hello {order.customer_name},</p>
                    <p>We've received your order and it's being processed. Here are your order details:</p>
                    
                    <div class="order-details">
                        <p><strong>Order Number:</strong> {order.order_id}</p>
                        <p><strong>Order Date:</strong> {order.order_date.strftime('%B %d, %Y %H:%M')}</p>
                        <p><strong>Total Amount:</strong> ₦{order.delivery_price:.2f}</p>
                    </div>

                    <p>You'll receive another email once your order is ready for {order.get_delivery_option_display()}.</p>

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
        
        # Get email settings from environment
        from_email = formataddr(("The Savory Bites Restaurant", settings.DEFAULT_FROM_EMAIL))
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=body_text.strip(),
            from_email=from_email,
            to=[order.customer_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        
        # Attach HTML version
        email.attach_alternative(body_html, "text/html")
        
        # Attach receipt PDF if provided
        if receipt:
            try:
                if is_file_object:
                    # Handle file-like object (production)
                    receipt.seek(0)  # Ensure we're at the start of the file
                    email.attach(
                        f'receipt_{order.order_id}.pdf',
                        receipt.read(),
                        'application/pdf'
                    )
                else:
                    # Handle file path (development)
                    full_path = os.path.join(settings.MEDIA_ROOT, receipt)
                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as pdf_file:
                            email.attach(
                                f'receipt_{order.order_id}.pdf',
                                pdf_file.read(),
                                'application/pdf'
                            )
            except Exception as e:
                print(f'Error attaching receipt to email: {str(e)}')
                # Continue without the receipt if there's an error
        
        # Send the email
        email.send(fail_silently=False)
        print(f'Order confirmation email sent to {order.customer_email}')
        return True
        
    except Exception as e:
        print(f'Failed to send order confirmation email: {str(e)}')
        # Log the full error for debugging
        import traceback
        print(traceback.format_exc())
        return False

def process_order_payment_confirmation(order):
    """
    Process an order after payment confirmation:
    1. Generate receipt PDF
    2. Send email with receipt
    3. Update order status if needed
    """
    try:
        print(f"Processing order payment confirmation for order {order.id}...")
        
        # Generate the receipt (returns either a path or a file-like object)
        receipt = generate_receipt_pdf(order)
        
        if receipt is None:
            print("Failed to generate receipt PDF")
            # Still try to send email without receipt
            return send_order_confirmation(order, None)
            
        try:
            # Send the receipt email
            if settings.DEBUG:
                # In development, pass the file path
                return send_order_confirmation(order, receipt)
            else:
                # In production, we pass the file-like object directly
                return send_order_confirmation(order, receipt, is_file_object=True)
        except Exception as e:
            print(f'Error sending order confirmation email: {str(e)}')
            return False
            
    except Exception as e:
        print(f'Error in process_order_payment_confirmation: {str(e)}')
        return False


