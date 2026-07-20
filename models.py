from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    credits = db.Column(db.Integer, default=30)
    ai_create_access_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reports = db.relationship('Report', backref='user', lazy=True)
    execution_plans = db.relationship('ExecutionPlan', backref='user', lazy=True)
    
    pm_access_expiry = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def deduct_credits(self, amount):
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False
    
    def add_credits(self, amount):
        self.credits += amount
    
    def __repr__(self):
        return f'<User {self.username}>'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    subcategory = db.Column(db.String(100))
    report_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, question, category=None, subcategory=None, report_content=None, user_id=None):
        self.question = question
        self.category = category
        self.subcategory = subcategory
        self.report_content = report_content
        self.user_id = user_id
    
    def __repr__(self):
        return f'<Report {self.id}: {self.question[:50]}...>'

class IndexContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_number = db.Column(db.Integer)
    
    def __init__(self, section, content, section_number=None):
        self.section = section
        self.content = content
        self.section_number = section_number
    
    def __repr__(self):
        return f'<IndexContent {self.section}>'

class ExecutionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String(100), nullable=False)
    problem_type = db.Column(db.Text, nullable=False)
    budget = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    timeline = db.Column(db.String(100), nullable=False)
    plan_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, event_type, problem_type, budget, currency, region, timeline, plan_content, user_id=None):
        self.event_type = event_type
        self.problem_type = problem_type
        self.budget = budget
        self.currency = currency
        self.region = region
        self.timeline = timeline
        self.plan_content = plan_content
        self.user_id = user_id
    
    def __repr__(self):
        return f'<ExecutionPlan {self.id}: {self.event_type}>'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, message):
        self.user_id = user_id
        self.message = message
    
    def __repr__(self):
        return f'<Feedback {self.id}: {self.message[:50]}...>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cashfree_order_id = db.Column(db.String(255), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    credits = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='PENDING')
    payment_method = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __init__(self, user_id, cashfree_order_id, amount, credits, currency='INR'):
        self.user_id = user_id
        self.cashfree_order_id = cashfree_order_id
        self.amount = amount
        self.currency = currency
        self.credits = credits
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.cashfree_order_id}>'

class MentorChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    messages = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id, topic, location, messages):
        self.user_id = user_id
        self.topic = topic
        self.location = location
        self.messages = messages
    
    def __repr__(self):
        return f'<MentorChat {self.id}: {self.topic}>'
