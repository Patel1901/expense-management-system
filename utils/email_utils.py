from flask_mail import Message, Mail

mail = Mail()

def send_otp_email(recipient_email, otp_code, user_name):
    try:
        msg = Message(
            subject='Your OTP Code - Expense Manager',
            recipients=[recipient_email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Welcome to Expense Manager!</h2>
                    <p>Hello {user_name},</p>
                    <p>Your One-Time Password (OTP) for verification is:</p>
                    <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                        {otp_code}
                    </div>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>Expense Manager Team</p>
                </body>
            </html>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

def send_approval_notification(recipient_email, expense_id, expense_amount, currency, user_name):
    try:
        msg = Message(
            subject='New Expense Awaiting Your Approval',
            recipients=[recipient_email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Expense Approval Required</h2>
                    <p>Hello {user_name},</p>
                    <p>A new expense has been submitted and requires your approval:</p>
                    <div style="background-color: #f9f9f9; padding: 15px; margin: 20px 0;">
                        <p><strong>Expense ID:</strong> #{expense_id}</p>
                        <p><strong>Amount:</strong> {currency} {expense_amount}</p>
                    </div>
                    <p>Please log in to the Expense Manager to review and approve/reject this expense.</p>
                    <br>
                    <p>Best regards,<br>Expense Manager Team</p>
                </body>
            </html>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False
