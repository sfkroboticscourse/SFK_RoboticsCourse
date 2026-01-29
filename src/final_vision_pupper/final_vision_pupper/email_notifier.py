#!/usr/bin/env python3
"""
Email Notification Node for Mini Pupper

Student Project: Send an email when a specific color/shape is detected.

This node subscribes to detection topics and sends an email when the target is found.
It includes a cooldown to prevent spamming emails.

SETUP REQUIRED:
1. Create an "App Password" for your Gmail account:
   - Go to https://myaccount.google.com/apppasswords
   - Generate a new app password for "Mail"
   - Use this password (not your regular password) in the config

2. Or use any SMTP server (Outlook, Yahoo, etc.)

Usage:
    # Start camera and detector first
    ros2 launch final_vision_pupper vision.launch.py mode:=color
    
    # Run email notifier
    ros2 run final_vision_pupper email_notifier --ros-args \
        -p target_color:=red \
        -p email_to:=recipient@example.com \
        -p email_from:=your.email@gmail.com \
        -p email_password:=your_app_password \
        -p email_subject:="Mini Pupper Alert!" \
        -p email_body:="I found something red!"

Parameters:
    target_color (str): Color that triggers email (default: 'red')
    min_area (int): Minimum detection area to trigger (default: 1000)
    cooldown_seconds (float): Minimum time between emails (default: 60.0)
    
    email_to (str): Recipient email address
    email_from (str): Sender email address  
    email_password (str): Sender email password (use App Password for Gmail)
    smtp_server (str): SMTP server (default: 'smtp.gmail.com')
    smtp_port (int): SMTP port (default: 587)
    
    email_subject (str): Email subject line
    email_body (str): Email body text
    include_details (bool): Include detection details in email (default: True)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailNotifier(Node):
    """Send email notifications when specific colors/shapes are detected."""
    
    def __init__(self):
        super().__init__('email_notifier')
        
        # Detection parameters
        self.declare_parameter('target_color', 'red')
        self.declare_parameter('min_area', 1000)
        self.declare_parameter('cooldown_seconds', 60.0)
        self.declare_parameter('detection_mode', 'color')  # 'color' or 'shape'
        
        # Email parameters
        self.declare_parameter('email_to', '')
        self.declare_parameter('email_from', '')
        self.declare_parameter('email_password', '')
        self.declare_parameter('smtp_server', 'smtp.gmail.com')
        self.declare_parameter('smtp_port', 587)
        self.declare_parameter('email_subject', 'Mini Pupper Detection Alert!')
        self.declare_parameter('email_body', 'Your Mini Pupper detected something!')
        self.declare_parameter('include_details', True)
        
        # Get parameters
        self.target_color = self.get_parameter('target_color').value
        self.min_area = self.get_parameter('min_area').value
        self.cooldown_seconds = self.get_parameter('cooldown_seconds').value
        self.detection_mode = self.get_parameter('detection_mode').value
        
        self.email_to = self.get_parameter('email_to').value
        self.email_from = self.get_parameter('email_from').value
        self.email_password = self.get_parameter('email_password').value
        self.smtp_server = self.get_parameter('smtp_server').value
        self.smtp_port = self.get_parameter('smtp_port').value
        self.email_subject = self.get_parameter('email_subject').value
        self.email_body = self.get_parameter('email_body').value
        self.include_details = self.get_parameter('include_details').value
        
        # State
        self.last_email_time = None
        self.emails_sent = 0
        
        # Validate email config
        if not self.email_to or not self.email_from or not self.email_password:
            self.get_logger().error("=" * 50)
            self.get_logger().error("EMAIL NOT CONFIGURED!")
            self.get_logger().error("Please provide: email_to, email_from, email_password")
            self.get_logger().error("Example:")
            self.get_logger().error("  ros2 run final_vision_pupper email_notifier --ros-args \\")
            self.get_logger().error("    -p email_to:=recipient@example.com \\")
            self.get_logger().error("    -p email_from:=sender@gmail.com \\")
            self.get_logger().error("    -p email_password:=your_app_password")
            self.get_logger().error("=" * 50)
            self.email_configured = False
        else:
            self.email_configured = True
        
        # Subscribe based on mode
        if self.detection_mode == 'shape':
            self.detection_sub = self.create_subscription(
                String, '/vision/shape_detected', self.shape_callback, 10)
            self.get_logger().info(f"Listening for {self.target_color} shapes")
        else:
            self.detection_sub = self.create_subscription(
                String, '/vision/colors_detected', self.color_callback, 10)
            self.get_logger().info(f"Listening for {self.target_color} color")
        
        self.get_logger().info(f"Email will be sent to: {self.email_to}")
        self.get_logger().info(f"Cooldown: {self.cooldown_seconds} seconds between emails")
    
    def color_callback(self, msg):
        """Handle color detection results."""
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        
        if not data.get('detected'):
            return
        
        # Check if target color is in detections
        details = data.get('details', {})
        if self.target_color in details:
            # Get the largest detection of this color
            detections = details[self.target_color]
            if detections:
                largest = max(detections, key=lambda x: x.get('area', 0))
                area = largest.get('area', 0)
                
                if area >= self.min_area:
                    self.trigger_email(f"Color: {self.target_color}", {
                        'area': area,
                        'centroid': largest.get('centroid'),
                        'all_colors': list(details.keys())
                    })
    
    def shape_callback(self, msg):
        """Handle shape detection results."""
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        
        if not data.get('detected'):
            return
        
        # Check if the detected color matches
        if data.get('color') == self.target_color:
            circles = data.get('circles', [])
            if circles:
                largest = circles[0]  # Already sorted by size
                radius = largest.get('radius', 0)
                area = 3.14159 * radius * radius  # Approximate area
                
                if area >= self.min_area:
                    self.trigger_email(f"Shape: {self.target_color} circle", {
                        'radius': radius,
                        'center': largest.get('center'),
                        'circularity': largest.get('circularity')
                    })
    
    def trigger_email(self, detection_type, details):
        """Send email if cooldown has passed."""
        now = datetime.now()
        
        # Check cooldown
        if self.last_email_time is not None:
            elapsed = (now - self.last_email_time).total_seconds()
            if elapsed < self.cooldown_seconds:
                remaining = self.cooldown_seconds - elapsed
                self.get_logger().debug(
                    f"Detected {detection_type} but in cooldown ({remaining:.0f}s remaining)")
                return
        
        # Send email
        success = self.send_email(detection_type, details, now)
        
        if success:
            self.last_email_time = now
            self.emails_sent += 1
            self.get_logger().info(f"📧 Email sent! (Total: {self.emails_sent})")
    
    def send_email(self, detection_type, details, timestamp):
        """Actually send the email."""
        if not self.email_configured:
            self.get_logger().warn("Email not configured, skipping send")
            return False
        
        try:
            # Build email
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = self.email_subject
            
            # Build body
            body = self.email_body + "\n\n"
            
            if self.include_details:
                body += "--- Detection Details ---\n"
                body += f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                body += f"Type: {detection_type}\n"
                for key, value in details.items():
                    body += f"{key}: {value}\n"
                body += "\n"
            
            body += "---\nSent by Mini Pupper Email Notifier"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send
            self.get_logger().info(f"Sending email to {self.email_to}...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            self.get_logger().info("Email sent successfully!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            self.get_logger().error("SMTP Authentication failed!")
            self.get_logger().error("For Gmail, make sure you're using an App Password:")
            self.get_logger().error("https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            self.get_logger().error(f"Failed to send email: {e}")
            return False


def main(args=None):
    rclpy.init(args=args)
    node = EmailNotifier()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
