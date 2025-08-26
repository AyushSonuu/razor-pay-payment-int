def get_email_template(user_name: str, batch_name: str, invite_link: str, payment_id: str = None) -> str:
    """
    Generate a beautiful HTML email template for the trading course invitation.
    """
    
    # Determine batch-specific content
    if batch_name.lower() == "morning":
        batch_icon = "🌅"
        batch_description = "Morning Trading Mastery"
        batch_features = [
            "Pre-market analysis techniques",
            "Gap trading strategies", 
            "Morning momentum plays",
            "Risk management protocols"
        ]
    else:
        batch_icon = "🌙"
        batch_description = "Evening Trading Excellence"
        batch_features = [
            "Swing trading strategies",
            "Position sizing techniques",
            "End-of-day analysis",
            "Portfolio management"
        ]
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to TopG Traders!</title>
        <style>
            /* Reset styles for email clients */
            body, table, td, p, a, li, blockquote {{
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }}
            table, td {{
                mso-table-lspace: 0pt;
                mso-table-rspace: 0pt;
            }}
            img {{
                -ms-interpolation-mode: bicubic;
                border: 0;
                height: auto;
                line-height: 100%;
                outline: none;
                text-decoration: none;
            }}
            
            /* Base styles */
            body {{
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #ffffff;
                line-height: 1.6;
            }}
            
            /* Email container */
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }}
            
            /* Header section */
            .header {{
                background: linear-gradient(135deg, #00d4ff 0%, #ff6b6b 50%, #4ecdc4 100%);
                padding: 40px 30px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="50" cy="10" r="0.5" fill="rgba(255,255,255,0.1)"/><circle cx="10" cy="60" r="0.5" fill="rgba(255,255,255,0.1)"/><circle cx="90" cy="40" r="0.5" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
                opacity: 0.3;
            }}
            
            .logo {{
                font-size: 2.5rem;
                font-weight: 800;
                color: #ffffff;
                margin-bottom: 10px;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                position: relative;
                z-index: 1;
            }}
            
            .tagline {{
                font-size: 1.1rem;
                color: rgba(255, 255, 255, 0.9);
                font-weight: 300;
                position: relative;
                z-index: 1;
            }}
            
            /* Welcome section */
            .welcome-section {{
                padding: 40px 30px;
                text-align: center;
                background: rgba(255, 255, 255, 0.05);
            }}
            
            .welcome-icon {{
                font-size: 4rem;
                margin-bottom: 20px;
                display: block;
            }}
            
            .welcome-title {{
                font-size: 2rem;
                font-weight: 700;
                color: #00d4ff;
                margin-bottom: 15px;
                text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            }}
            
            .welcome-message {{
                font-size: 1.1rem;
                color: #b0b0b0;
                margin-bottom: 30px;
                line-height: 1.6;
            }}
            
            /* Course details section */
            .course-section {{
                padding: 30px;
                background: rgba(0, 212, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.3);
                margin: 0 30px;
                border-radius: 15px;
                text-align: center;
            }}
            
            .course-badge {{
                display: inline-block;
                background: linear-gradient(135deg, #00d4ff, #ff6b6b);
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                font-weight: 700;
                font-size: 1.1rem;
                margin-bottom: 20px;
                box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
            }}
            
            .course-description {{
                color: #ffffff;
                font-size: 1.1rem;
                margin-bottom: 25px;
            }}
            
            .features-list {{
                list-style: none;
                padding: 0;
                margin: 0;
                text-align: left;
            }}
            
            .features-list li {{
                color: #b0b0b0;
                margin-bottom: 10px;
                padding-left: 25px;
                position: relative;
            }}
            
            .features-list li::before {{
                content: '✓';
                position: absolute;
                left: 0;
                color: #00d4ff;
                font-weight: bold;
                font-size: 1.1rem;
            }}
            
            /* Telegram section */
            .telegram-section {{
                padding: 40px 30px;
                background: linear-gradient(135deg, rgba(0, 136, 204, 0.2), rgba(0, 136, 204, 0.1));
                border: 2px solid rgba(0, 136, 204, 0.3);
                margin: 30px;
                border-radius: 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .telegram-section::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(0, 136, 204, 0.1) 0%, transparent 70%);
                animation: rotate 20s linear infinite;
            }}
            
            .telegram-content {{
                position: relative;
                z-index: 1;
            }}
            
            .telegram-icon {{
                font-size: 3rem;
                margin-bottom: 20px;
                display: block;
            }}
            
            .telegram-title {{
                font-size: 1.5rem;
                color: #00bfff;
                margin-bottom: 15px;
                font-weight: 600;
            }}
            
            .telegram-description {{
                color: #ffffff;
                margin-bottom: 25px;
                line-height: 1.6;
            }}
            
            .invite-link-container {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                word-break: break-all;
                font-family: monospace;
                font-size: 0.9rem;
                color: #00d4ff;
            }}
            
            .join-button {{
                display: inline-block;
                background: linear-gradient(135deg, #0088cc, #00bfff);
                color: white;
                text-decoration: none;
                padding: 15px 40px;
                border-radius: 25px;
                font-weight: 600;
                font-size: 1.1rem;
                margin: 15px 10px;
                box-shadow: 0 5px 15px rgba(0, 136, 204, 0.3);
                transition: all 0.3s ease;
            }}
            
            .join-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 136, 204, 0.4);
            }}
            
            /* Payment details */
            .payment-section {{
                padding: 30px;
                background: rgba(255, 255, 255, 0.05);
                margin: 0 30px;
                border-radius: 15px;
                text-align: center;
            }}
            
            .payment-title {{
                font-size: 1.2rem;
                color: #00d4ff;
                margin-bottom: 20px;
            }}
            
            .payment-details {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 15px 25px;
                color: #ffffff;
                font-family: monospace;
                font-size: 0.9rem;
            }}
            
            /* Footer */
            .footer {{
                padding: 30px;
                text-align: center;
                background: rgba(0, 0, 0, 0.3);
            }}
            
            .footer-text {{
                color: #888;
                font-size: 0.9rem;
                margin-bottom: 15px;
            }}
            
            .social-links {{
                margin-top: 20px;
            }}
            
            .social-link {{
                display: inline-block;
                margin: 0 10px;
                color: #00d4ff;
                text-decoration: none;
                font-size: 1.2rem;
            }}
            
            /* Responsive design */
            @media only screen and (max-width: 600px) {{
                .email-container {{
                    margin: 0;
                    border-radius: 0;
                }}
                
                .header, .welcome-section, .course-section, .telegram-section, .payment-section, .footer {{
                    padding: 20px 15px;
                    margin: 0 15px;
                }}
                
                .logo {{
                    font-size: 2rem;
                }}
                
                .welcome-title {{
                    font-size: 1.5rem;
                }}
                
                .telegram-section {{
                    margin: 15px;
                }}
            }}
            
            /* Animation keyframes */
            @keyframes rotate {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
            
            @keyframes glow {{
                0%, 100% {{ filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.5)); }}
                50% {{ filter: drop-shadow(0 0 30px rgba(255, 107, 107, 0.5)); }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <div class="logo">TopG Traders</div>
                <div class="tagline">Master the Markets • Dominate Trading • Build Wealth</div>
            </div>
            
            <!-- Welcome Section -->
            <div class="welcome-section">
                <span class="welcome-icon">🎉</span>
                <h1 class="welcome-title">Welcome to the Elite Trading Community!</h1>
                <p class="welcome-message">
                    Hi {user_name},<br><br>
                    Congratulations on taking the first step towards financial freedom! You've just joined an exclusive community of successful traders who are mastering the markets and building wealth through strategic trading.
                </p>
            </div>
            
            <!-- Course Details -->
            <div class="course-section">
                <div class="course-badge">{batch_icon} {batch_description}</div>
                <p class="course-description">
                    You've successfully enrolled in our comprehensive {batch_name.lower()} trading program. Get ready to transform your trading skills and achieve financial success!
                </p>
                <ul class="features-list">
                    {''.join([f'<li>{feature}</li>' for feature in batch_features])}
                    <li>Live trading sessions</li>
                    <li>Lifetime access to updates</li>
                    <li>Exclusive market insights</li>
                </ul>
            </div>
            
            <!-- Telegram Section -->
            <div class="telegram-section">
                <div class="telegram-content">
                    <span class="telegram-icon">📱</span>
                    <h2 class="telegram-title">Join Your Exclusive Trading Group</h2>
                    <p class="telegram-description">
                        Connect with fellow traders, get real-time market insights, and access exclusive trading signals. Your private Telegram group is ready for you!
                    </p>
                    
                    <div class="invite-link-container">
                        {invite_link}
                    </div>
                    
                    <a href="{invite_link}" class="join-button">
                        🚀 Join Trading Group
                    </a>
                    
                    <p style="color: #888; font-size: 0.9rem; margin-top: 20px;">
                        <strong>Important:</strong> This invite link is valid for 24 hours and can be used once. 
                        If you have any issues, please contact our support team.
                    </p>
                </div>
            </div>
            
            <!-- Payment Confirmation -->
            <div class="payment-section">
                <h3 class="payment-title">📊 Payment Confirmation</h3>
                <div class="payment-details">
                    Amount: ₹16,999<br>
                    Status: ✅ Completed<br>
                    {f'Payment ID: {payment_id}' if payment_id else ''}
                </div>
            </div>
            
            <!-- Next Steps -->
            <div class="welcome-section" style="background: rgba(255, 255, 255, 0.02);">
                <h2 style="color: #00d4ff; margin-bottom: 20px;">🚀 What Happens Next?</h2>
                <div style="text-align: left; max-width: 400px; margin: 0 auto;">
                    <div style="margin-bottom: 15px; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; color: #00d4ff; font-weight: bold;">1.</span>
                        <span style="color: #ffffff;">✅ Payment processed successfully</span>
                    </div>
                    <div style="margin-bottom: 15px; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; color: #00d4ff; font-weight: bold;">2.</span>
                        <span style="color: #ffffff;">📱 Join the Telegram trading group</span>
                    </div>
                    <div style="margin-bottom: 15px; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; color: #00d4ff; font-weight: bold;">3.</span>
                        <span style="color: #ffffff;">📧 Check your email for course materials</span>
                    </div>
                    <div style="margin-bottom: 15px; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; color: #00d4ff; font-weight: bold;">4.</span>
                        <span style="color: #ffffff;">🎯 Start your trading journey!</span>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p class="footer-text">
                    Thank you for choosing TopG Traders!<br>
                    We're excited to be part of your trading success story.
                </p>
                <p class="footer-text">
                    <strong>Need Help?</strong><br>
                    Contact us at support@topgtraders.com<br>
                    or reply to this email for assistance.
                </p>
                <div class="social-links">
                    <a href="#" class="social-link">📧</a>
                    <a href="#" class="social-link">📱</a>
                    <a href="#" class="social-link">💬</a>
                </div>
                <p class="footer-text" style="font-size: 0.8rem; margin-top: 20px;">
                    © 2024 TopG Traders. All rights reserved.<br>
                    This email was sent to you because you enrolled in our trading course.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template 