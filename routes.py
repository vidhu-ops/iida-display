from flask import render_template, request, redirect, url_for, flash, jsonify, session, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import Report, IndexContent, User, ExecutionPlan, Feedback, Payment, MentorChat
from pdf_processor import PDFProcessor, initialize_pdf_content
from gemini_service import GeminiService, test_gemini_connection
from mentor_service import get_mentor_response
import logging
import os
import uuid
import requests
import json
from datetime import datetime, timedelta

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/png')

@app.route('/')
def index():
    """Home page with embedded website - show for all users"""
    return render_template('home.html')

@app.route('/analyse')
def analyse():
    """Analyse page with research form"""
    # Check if index content is loaded
    content_count = IndexContent.query.count()
    if content_count == 0:
        # Initialize PDF content
        if initialize_pdf_content():
            flash('Knowledge base initialized successfully!', 'success')
        else:
            flash('Warning: Knowledge base could not be initialized. Some features may not work properly.', 'warning')
    
    # Get dropdown options
    processor = PDFProcessor('attached_assets/Lesson plan (1)_1754664072794.pdf')
    categories_dict = processor.get_dropdown_options()
    
    # Structure dropdown options for template and JavaScript
    dropdown_options = {
        'categories': list(categories_dict.keys()),
        'subcategories': categories_dict
    }
    
    # Test Gemini connection
    gemini_status = test_gemini_connection()
    if not gemini_status:
        flash('Warning: Gemini API connection failed. Please check your API key configuration.', 'warning')
    
    # Get recent plans instead of reports
    recent_plans = ExecutionPlan.query.filter_by(user_id=current_user.id).order_by(ExecutionPlan.created_at.desc()).limit(5).all() if current_user.is_authenticated else []
    
    return render_template('analyse.html', 
                         dropdown_options=dropdown_options,
                         recent_plans=recent_plans,
                         gemini_status=gemini_status)

@app.route('/api/competitive-analysis', methods=['POST'])
@login_required
def api_competitive_analysis():
    try:
        data = request.get_json() or {}
        idea = data.get('idea', '').strip()
        industry = data.get('industry', '').strip()
        location = data.get('location', '').strip()

        if not idea or not industry or not location:
            return jsonify({'error': 'Missing required fields'}), 400

        gemini_service = GeminiService()
        analysis = gemini_service.generate_competitive_analysis(idea, industry, location)

        if not analysis:
            return jsonify({'error': 'Failed to generate competitive analysis. Please try again.'}), 500

        return jsonify({'analysis': analysis})
    except Exception as e:
        logging.error(f"Competitive analysis error: {e}")
        return jsonify({'error': f'Server error generating competitive analysis: {str(e)}'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user directly"""
    if current_user.is_authenticated:
        return redirect(url_for('analyse'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate inputs
        if not username or not email or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('register'))
            
        # Create user directly without OTP
        user = User()
        user.username = username
        user.email = email
        user.credits = 0
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # If user has temporary chats in the request (from localStorage), save them
            temp_chats = request.form.get('temp_chats')
            if temp_chats:
                try:
                    import json
                    chats_data = json.loads(temp_chats)
                    for chat_data in chats_data:
                        mentor_chat = MentorChat(
                            user_id=user.id,
                            topic=chat_data.get('topic', ''),
                            location=chat_data.get('location', ''),
                            messages=json.dumps(chat_data.get('messages', []))
                        )
                        db.session.add(mentor_chat)
                    db.session.commit()
                except Exception as e:
                    logging.warning(f"Could not import temporary chats: {e}")
            
            flash(f'Account created successfully! You have been given 30 credits to get started.', 'success')
            login_user(user)
            return redirect(url_for('analyse'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating user: {e}")
            flash('Error creating account. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/mentor')
def mentor():
    """Mentor chat page"""
    return render_template('mentor.html')

@app.route('/mentor_chat', methods=['POST'])
def mentor_chat():
    """Handle mentor chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        topic = data.get('topic', '').strip()
        location = data.get('location', '').strip()
        message_count = data.get('message_count', 0)
        
        if not message or not topic or not location:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Non-logged-in user: max 8 messages
        if not current_user.is_authenticated:
            if message_count >= 8:
                return jsonify({'error': 'signup_required', 'message': 'Sign up to continue mentoring'}), 403
        else:
            charge_required = message_count >= 8 and (message_count - 8) % 10 == 0
            if charge_required:
                if current_user.credits < 1:
                    return jsonify({'error': 'credits_needed', 'message': 'You need 1 credit to continue. Please recharge.'}), 402
                if not current_user.deduct_credits(1):
                    return jsonify({'error': 'credits_failed', 'message': 'Failed to deduct credits'}), 500
                db.session.commit()
        
        response, error = get_mentor_response(message, topic, location)
        
        if error:
            # Restore credits if API call failed
            if current_user.is_authenticated and message_count >= 8 and (message_count - 8) % 10 == 0:
                current_user.add_credits(1)
                db.session.commit()
            logging.warning(f"Mentor response error: {error}")
            return jsonify({'error': error}), 500
        
        # Save to database if logged in
        if current_user.is_authenticated:
            import json
            chat = MentorChat.query.filter_by(user_id=current_user.id, topic=topic, location=location).first()
            if not chat:
                chat = MentorChat(current_user.id, topic, location, json.dumps([]), is_temporary=False, total_messages=0)
                db.session.add(chat)
            
            messages = json.loads(chat.messages)
            messages.append({'sender': 'user', 'text': message})
            messages.append({'sender': 'mentor', 'text': response})
            chat.messages = json.dumps(messages)
            chat.total_messages = len(messages) // 2
            db.session.commit()
        
        return jsonify({'response': response, 'credits_remaining': current_user.credits if current_user.is_authenticated else None})
    
    except Exception as e:
        logging.error(f"Mentor chat error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/mentor_save_chat', methods=['POST'])
@login_required
def mentor_save_chat():
    """Save mentor chat as a new session"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        location = data.get('location', '').strip()
        
        chat = MentorChat.query.filter_by(user_id=current_user.id, topic=topic, location=location).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        return jsonify({'success': True, 'chat_id': chat.id})
    except Exception as e:
        logging.error(f"Save chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/mentor_download_chat', methods=['POST'])
def mentor_download_chat():
    """Download chat as text file"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        location = data.get('location', '').strip()
        messages_json = data.get('messages', '[]')
        
        import json
        messages = json.loads(messages_json)
        
        text_content = f"Mentor Chat: {topic}\nLocation: {location}\n" + "="*50 + "\n\n"
        for msg in messages:
            sender = "You" if msg['sender'] == 'user' else "Mentor"
            text_content += f"{sender}:\n{msg['text']}\n\n"
        
        return jsonify({'content': text_content, 'filename': f'mentor-chat-{topic.lower().replace(" ", "-")}.txt'})
    except Exception as e:
        logging.error(f"Download chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/mentor-chats')
@login_required
def mentor_chats():
    """View the current user's mentor chats"""
    try:
        return redirect(url_for('mentor_my_chat'))
    except Exception as e:
        logging.error(f"Error loading mentor chats: {e}")
        flash('Error loading chats.', 'error')
        return redirect(url_for('mentor'))

@app.route('/mentor-chat/<int:chat_id>')
@login_required
def view_mentor_chat(chat_id):
    """View a specific mentor chat"""
    try:
        chat = MentorChat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not chat:
            flash('Chat not found.', 'error')
            return redirect(url_for('mentor_chats'))
        
        import json
        messages = json.loads(chat.messages)
        return render_template('view_mentor_chat.html', chat=chat, messages=messages)
    except Exception as e:
        logging.error(f"Error loading chat: {e}")
        flash('Error loading chat.', 'error')
        return redirect(url_for('mentor_chats'))

@app.route('/mentor-my-chat')
@login_required
def mentor_my_chat():
    """Open the current user's latest mentor chat"""
    try:
        chat = MentorChat.query.filter_by(user_id=current_user.id).order_by(MentorChat.updated_at.desc()).first()
        if not chat:
            flash('No mentor chat found yet.', 'error')
            return redirect(url_for('mentor'))
        import json
        messages = json.loads(chat.messages)
        return render_template('view_mentor_chat.html', chat=chat, messages=messages)
    except Exception as e:
        logging.error(f"Error loading latest mentor chat: {e}")
        flash('Error loading chat.', 'error')
        return redirect(url_for('mentor'))

@app.route('/financial-tools')
def financial_tools():
    """Financial projection tools page"""
    return render_template('financial_tools.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login user"""
    if current_user.is_authenticated:
        return redirect(url_for('analyse'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter username and password.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
        
        login_user(user)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('analyse'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate a comprehensive research report"""
    if not current_user.is_authenticated:
        flash('Please log in or register to generate reports.', 'error')
        return redirect(url_for('login'))
    
    report = None
    try:
        question = request.form.get('question', '').strip()
        
        if not question:
            flash('Please enter a research question.', 'error')
            return redirect(url_for('analyse'))
        
        if len(question) < 10:
            flash('Please provide a more detailed research question (at least 10 characters).', 'warning')
            return redirect(url_for('analyse'))
        
        # Fixed cost for dynamic reports
        credits_needed = 10
        
        # Check if user has enough credits
        if current_user.credits < credits_needed:
            flash(f'Insufficient credits. You need {credits_needed} credits but have {current_user.credits}.', 'error')
            return redirect(url_for('analyse'))
        
        # Deduct credits
        current_user.deduct_credits(credits_needed)
        db.session.commit()
        
        # Generate initial report structure using Gemini
        try:
            gemini_service = GeminiService()
            report_content = gemini_service.generate_comprehensive_report(question)
        except Exception as gen_error:
            logging.error(f"Error generating report structure: {gen_error}")
            flash('Error initializing report. Please try again.', 'error')
            return redirect(url_for('analyse'))
        
        # Save report to database
        try:
            report = Report(
                question=question,
                report_content=report_content,
                user_id=current_user.id
            )
            db.session.add(report)
            db.session.commit()
            
            flash('Research initialized! Click sections to load details.', 'success')
            return redirect(url_for('view_report', report_id=report.id))
            
        except Exception as db_save_error:
            logging.error(f"Database error saving report: {db_save_error}")
            db.session.rollback()
            flash('Error saving report to database.', 'error')
            return redirect(url_for('analyse'))
        
    except Exception as e:
        logging.error(f"Unexpected error in generate_report: {e}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('analyse'))

@app.route('/report/<int:report_id>')
def view_report(report_id):
    """View a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        return render_template('report.html', report=report)
    except Exception as e:
        logging.error(f"Error viewing report {report_id}: {e}")
        flash('Error loading report. The report may have been deleted or is unavailable.', 'error')
        return redirect(url_for('index'))

@app.route('/api/generate_section', methods=['POST'])
@login_required
def generate_section():
    """Endpoint to generate an individual section dynamically"""
    data = request.json
    question = data.get('question')
    category = data.get('category')
    subcategory = data.get('subcategory')
    section_id = data.get('section_id')
    
    if question is None or section_id is None:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    try:
        gemini_service = GeminiService()
        content = gemini_service.generate_section(question, category, subcategory, int(section_id))
        return jsonify({'content': content})
    except Exception as e:
        logging.error(f"Error in dynamic section generation: {e}")
        return jsonify({'error': 'Failed to generate section content'}), 500

@app.route('/reports')
def list_reports():
    """List all reports and execution plans"""
    if not current_user.is_authenticated:
        flash('Please log in to view your reports.', 'error')
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    
    # Fetch execution plans
    execution_plans = ExecutionPlan.query.filter_by(user_id=current_user.id).order_by(ExecutionPlan.created_at.desc()).all()
    
    # Combined items list with plans prioritized
    all_items = []
    for plan in execution_plans:
        all_items.append({
            'type': 'plan',
            'id': plan.id,
            'created_at': plan.created_at,
            'title': f"{plan.event_type} - {plan.problem_type[:50]}",
            'event_type': plan.event_type,
            'budget': plan.budget,
            'currency': plan.currency,
            'region': plan.region,
            'data': plan
        })
    
    # Sort by date descending
    all_items.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('reports_list.html', items=all_items, plans=execution_plans)

@app.route('/buy-credits')
@login_required
def buy_credits():
    """Page to purchase more credits"""
    credit_packages = [
        {'credits': 10, 'price': 850, 'discount': 0},
        {'credits': 30, 'price': 2200, 'discount': 0},
    ]
    return render_template('payments.html', packages=credit_packages, user_credits=current_user.credits)

@app.route('/debug/users')
def debug_users():
    """Debug: View all users in database"""
    try:
        users = User.query.all()
        user_data = []
        for user in users:
            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'credits': user.credits,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'
            })
        return jsonify({'status': 'success', 'total_users': len(user_data), 'users': user_data})
    except Exception as e:
        logging.error(f"Debug users error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/payments')
def debug_payments():
    """Debug: View all payments in database"""
    try:
        payments = Payment.query.all()
        payment_data = []
        for payment in payments:
            user = User.query.get(payment.user_id)
            payment_data.append({
                'id': payment.id,
                'order_id': payment.cashfree_order_id,
                'user_id': payment.user_id,
                'username': user.username if user else 'N/A',
                'amount': payment.amount,
                'credits': payment.credits,
                'status': payment.status,
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else 'N/A',
                'completed_at': payment.completed_at.strftime('%Y-%m-%d %H:%M:%S') if payment.completed_at else 'N/A'
            })
        return jsonify({'status': 'success', 'total_payments': len(payment_data), 'payments': payment_data})
    except Exception as e:
        logging.error(f"Debug payments error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/user-credits')
@login_required
def api_user_credits():
    """API endpoint to get current user's credits"""
    try:
        db.session.refresh(current_user)
        return jsonify({
            'status': 'success',
            'user_id': current_user.id,
            'username': current_user.username,
            'credits': current_user.credits
        })
    except Exception as e:
        logging.error(f"Error fetching user credits: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/verify-payment/<order_id>')
def api_verify_payment(order_id):
    """Verify payment status with Cashfree and add credits if paid"""
    try:
        logging.info(f"Payment verification API called: order_id={order_id}")
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
        
        # If already completed, return success
        if payment.status == 'COMPLETED':
            user = User.query.get(payment.user_id)
            return jsonify({
                'status': 'success',
                'payment_status': 'COMPLETED',
                'user': user.username if user else 'Unknown',
                'credits': payment.credits,
                'message': 'Payment already processed'
            })
        
        # Verify with Cashfree API
        app_id = os.getenv('CASHFREE_APP_ID')
        api_key = os.getenv('CASHFREE_API_KEY')
        cashfree_api_url = os.getenv('CASHFREE_API_URL', 'https://api.cashfree.com/pg')
        
        if not app_id or not api_key:
            return jsonify({'status': 'error', 'message': 'Payment gateway not configured'}), 500
        
        headers = {
            'accept': 'application/json',
            'x-client-id': app_id,
            'x-client-secret': api_key,
            'x-api-version': '2023-08-01'
        }
        
        response = requests.get(
            f'{cashfree_api_url}/orders/{order_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            order_status = data.get('order_status', '')
            
            logging.info(f"Cashfree response: order_id={order_id}, order_status={order_status}")
            
            if order_status == 'PAID':
                # Payment is PAID - add credits
                user = User.query.get(payment.user_id)
                if user:
                    initial_balance = user.credits
                    payment.status = 'COMPLETED'
                    payment.completed_at = datetime.utcnow()
                    user.add_credits(payment.credits)
                    db.session.commit()
                    db.session.refresh(user)
                    
                    logging.info(f"✓ Payment verified and completed: order_id={order_id}, user={user.username}, credits_added={payment.credits}, balance={initial_balance}→{user.credits}")
                    
                    return jsonify({
                        'status': 'success',
                        'payment_status': 'COMPLETED',
                        'user': user.username,
                        'credits': payment.credits,
                        'new_balance': user.credits,
                        'message': f'{payment.credits} credits added to your account'
                    })
                else:
                    return jsonify({'status': 'error', 'message': 'User not found'}), 404
            else:
                # Payment not yet paid
                return jsonify({
                    'status': 'pending',
                    'payment_status': order_status,
                    'message': 'Payment is still processing'
                })
        else:
            logging.error(f"Cashfree API error: {response.status_code} - {response.text}")
            return jsonify({'status': 'error', 'message': 'Failed to verify payment with gateway'}), 500
            
    except Exception as e:
        logging.error(f"Payment verification error: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/test/create-dummy-payment')
@login_required
def test_create_dummy_payment():
    """Create a dummy payment for testing purposes"""
    try:
        from uuid import uuid4
        
        order_id = f"TEST_{uuid4().hex[:12].upper()}"
        credits = 10
        amount = 850
        
        payment = Payment(
            user_id=current_user.id,
            cashfree_order_id=order_id,
            amount=amount,
            credits=credits,
            currency='INR'
        )
        payment.status = 'PENDING'
        db.session.add(payment)
        db.session.commit()
        
        logging.info(f"Test payment created: order_id={order_id}, user={current_user.username}, credits={credits}")
        
        return jsonify({
            'status': 'success',
            'message': 'Test payment created successfully',
            'order_id': order_id,
            'user_id': current_user.id,
            'username': current_user.username,
            'credits_to_add': credits,
            'current_balance': current_user.credits,
            'callback_url': f"/payment-callback?order_id={order_id}&order_status=PAID"
        })
    except Exception as e:
        logging.error(f"Error creating test payment: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/deduct_credits', methods=['POST'])
@login_required
def api_deduct_credits():
    """API endpoint to deduct credits from user's account"""
    if current_user.credits < 10:
        return jsonify({'error': 'Insufficient credits', 'redirect': '/buy-credits'}), 402

    try:
        current_user.deduct_credits(10)
        db.session.commit()
        return jsonify({'success': True, 'remaining_credits': current_user.credits})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deducting credits: {e}")
        return jsonify({'error': 'Failed to deduct credits'}), 500

@app.route('/initialize_content')
def initialize_content():
    """Manually initialize PDF content"""
    if initialize_pdf_content():
        flash('Knowledge base initialized successfully!', 'success')
    else:
        flash('Failed to initialize knowledge base.', 'error')
    return redirect(url_for('index'))

@app.route('/test_gemini')
def test_gemini():
    """Test Gemini API connection"""
    status = test_gemini_connection()
    if status:
        flash('Gemini API connection successful!', 'success')
    else:
        flash('Gemini API connection failed. Please check your API key.', 'error')
    return redirect(url_for('index'))

@app.route('/shortcode.html')
def shortcode():
    """Serve the shortcode integration page"""
    return render_template('shortcode.html')

@app.route('/integration-guide')
def integration_guide():
    """Serve the integration guide as HTML"""
    try:
        with open('INTEGRATION_GUIDE.md', 'r') as f:
            content = f.read()
        return render_template('markdown_view.html', content=content)
    except Exception as e:
        logging.error(f"Error loading integration guide: {e}")
        return "Integration guide not found", 404

@app.route('/saved-plans')
@login_required
def saved_plans():
    """Display list of saved execution plans"""
    plans = ExecutionPlan.query.filter_by(user_id=current_user.id).order_by(ExecutionPlan.created_at.desc()).all()
    return render_template('saved_plans.html', plans=plans)

@app.route('/plan/<int:plan_id>')
@login_required
def view_plan(plan_id):
    """View a saved execution plan"""
    plan = ExecutionPlan.query.get_or_404(plan_id)
    
    # Check ownership
    if plan.user_id != current_user.id:
        flash('You do not have permission to view this plan.', 'error')
        return redirect(url_for('saved_plans'))
    
    return render_template('plan_view.html', plan=plan)

@app.route('/plan-it-out', methods=['GET', 'POST'])
def plan_it_out():
    """Plan It Out - Create execution plans with Gemini"""
    if not current_user.is_authenticated:
        flash('Please log in or register to create plans.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            event_type = request.form.get('event_type', '').strip()
            problem_type = request.form.get('problem_type', '').strip()
            budget = request.form.get('budget', '').strip()
            currency = request.form.get('currency', 'USD')
            region = request.form.get('region', '').strip()
            timeline = request.form.get('timeline', '').strip()
            
            if not event_type or not problem_type or not budget or not region or not timeline:
                flash('Please fill in all fields.', 'error')
                return redirect(url_for('plan_it_out'))
            
            if len(problem_type) < 20:
                flash('Please provide a more detailed problem description (at least 20 characters).', 'warning')
                return redirect(url_for('plan_it_out'))
            
            # Credit check - 10 credits for planning
            credits_needed = 10
            if current_user.credits < credits_needed:
                flash(f'Insufficient credits. You need {credits_needed} credits but have {current_user.credits}. Please buy credits to continue.', 'error')
                return redirect(url_for('buy_credits'))
            
            # Deduct credits before generating
            current_user.deduct_credits(credits_needed)
            db.session.commit()
            
            # Generate execution plan
            gemini_service = GeminiService()
            plan_content = gemini_service.generate_execution_plan(event_type, problem_type, budget, currency, region, timeline)
            
            if not plan_content:
                # Refund if failed
                current_user.credits += credits_needed
                db.session.commit()
                flash('AI generation failed. Credits refunded.', 'error')
                return redirect(url_for('plan_it_out'))
            
            # Save the execution plan to database
            try:
                execution_plan = ExecutionPlan(
                    event_type=event_type,
                    problem_type=problem_type,
                    budget=budget,
                    currency=currency,
                    region=region,
                    timeline=timeline,
                    plan_content=plan_content,
                    user_id=current_user.id
                )
                db.session.add(execution_plan)
                db.session.commit()
                logging.info(f"Successfully saved plan {execution_plan.id} for user {current_user.id}")
            except Exception as e:
                logging.error(f"Failed to save plan to database: {e}")
                db.session.rollback()
                flash('Warning: Plan was generated but could not be saved to your history.', 'warning')
            
            return render_template('plan_it_out_result.html', 
                                 plan_content=plan_content,
                                 event_type=event_type,
                                 problem_type=problem_type,
                                 budget=budget,
                                 currency=currency,
                                 region=region,
                                 timeline=timeline)
        
        except Exception as e:
            logging.error(f"Error in plan_it_out: {e}")
            flash('An error occurred while generating your plan. Please try again.', 'error')
            return redirect(url_for('plan_it_out'))
    
    return render_template('plan_it_out.html')

@app.route('/execute')
def execute_page():
    """Display the embedded website for execution"""
    return render_template('embedded_website.html')

@app.route('/project-management')
@login_required
def project_management():
    """Display the project management platform with credit-based access"""
    now = datetime.utcnow()
    
    # Check if access is still valid
    if current_user.pm_access_expiry and current_user.pm_access_expiry > now:
        return render_template('project_management.html')
    
    # Check if user wants to unlock
    if request.args.get('unlock') == 'true':
        credits_needed = 25
        if current_user.credits >= credits_needed:
            # Atomic update to avoid race conditions if possible, but standard SQLAlchemy here
            current_user.credits -= credits_needed
            current_user.pm_access_expiry = now + timedelta(days=30)
            db.session.commit()
            flash('Project Management tools unlocked for 30 days!', 'success')
            return redirect(url_for('project_management'))
        else:
            flash(f'Insufficient credits. You need {credits_needed} credits to unlock Project Management.', 'error')
            return redirect(url_for('buy_credits'))
            
    return render_template('project_management_lock.html', expiry=current_user.pm_access_expiry)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chatbot endpoint for the IDA Assistant"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'response': 'How can I help you today?'})
            
        # Use Gemini to generate a response
        gemini_service = GeminiService()
        response_text = gemini_service.generate_chat_response(user_message)
        
        return jsonify({'response': response_text})
    except Exception as e:
        logging.error(f"Chatbot error: {e}")
        return jsonify({'response': "I'm sorry, I'm having trouble connecting to my brain right now. Please try again later."}), 500


@app.route('/analysis-reports')
def analysis_reports():
    """Display analysis reports from famous business sources"""
    # Real business reports from famous sources for 2025
    reports = [
        {
            'id': 1,
            'title': 'Global Business Outlook 2025',
            'source': 'McKinsey & Company',
            'date': 'January 2025',
            'summary': 'McKinsey\'s comprehensive analysis reveals that businesses focusing on AI integration and digital transformation are seeing 23% higher productivity gains. The report emphasizes the critical importance of supply chain resilience, with companies investing in diversification experiencing 18% better margins. Key findings include: (1) AI adoption accelerating across manufacturing, healthcare, and finance sectors; (2) Geopolitical tensions requiring strategic supply chain redesign; (3) Talent retention emerging as top C-suite concern with 42% of executives citing skills gaps; (4) ESG commitments becoming competitive necessity, not optional.',
            'category': 'Economic Trends',
            'insights': [
                'AI investment ROI averaging 3.5x over 2 years',
                'Supply chain costs up 12% but resilience investments reducing risk by 28%',
                'Digital talent shortage creating wage premium of 15-20%',
                'Sustainable practices improving brand value by 8-12%'
            ]
        },
        {
            'id': 2,
            'title': 'Future of Enterprise Technology',
            'source': 'Gartner',
            'date': 'February 2025',
            'summary': 'Gartner\'s latest research shows cloud adoption reaching 87% of enterprises globally, with hybrid and multi-cloud strategies dominating. The report highlights critical technology priorities: (1) Cybersecurity investments up 34% YoY as breach costs average $4.45M; (2) AI and machine learning driving $2.3T in business value creation; (3) Workforce automation enabling net job growth despite displacement concerns; (4) Data governance becoming strategic imperative with 91% of companies viewing it as critical. IT spending projected to grow 7.2% reaching $5.15T globally.',
            'category': 'Technology',
            'insights': [
                'Cloud infrastructure spending up 24% year-over-year',
                'Cybersecurity represents 13.2% of IT budgets globally',
                'AI/ML projects seeing 65% success rate in enterprise settings',
                'Data analytics investments providing 9:1 return on investment'
            ]
        },
        {
            'id': 3,
            'title': 'Financial Markets & Investment Trends Q1 2025',
            'source': 'Goldman Sachs',
            'date': 'March 2025',
            'summary': 'Goldman Sachs equity research division reports strong fundamentals underpinning market expansion. Key trends: (1) Earnings growth of 9.7% expected for S&P 500 in 2025; (2) Technology sector maintaining dominance with 35% of index weight; (3) Energy transition creating $2.1T investment opportunity; (4) Interest rate stabilization improving consumer spending outlook; (5) Corporate buybacks reaching $850B in first half, supporting valuations. Healthcare and renewable energy emerging as best performing sectors.',
            'category': 'Markets & Finance',
            'insights': [
                'S&P 500 earnings growth forecast: 9.7% for 2025',
                'Tech sector allocation at 35% of portfolio recommendations',
                'Energy transition investments to reach $2.1T cumulatively',
                'Credit spreads tightening, indicating economic confidence'
            ]
        },
        {
            'id': 4,
            'title': 'Consumer Behavior & Retail Transformation',
            'source': 'Boston Consulting Group',
            'date': 'February 2025',
            'summary': 'BCG analyzes shifting consumer preferences and retail evolution. Major findings: (1) E-commerce now 28% of retail sales globally, growing 15% annually; (2) Omnichannel strategies essential, with 76% of consumers expecting seamless experiences; (3) Personalization driving 25% higher conversion rates and 20% increased customer lifetime value; (4) Sustainability influencing 43% of purchase decisions across demographics; (5) Social commerce generating $720B in revenue. Retailers investing in AI-driven personalization and supply chain visibility gaining competitive advantage.',
            'category': 'Consumer & Retail',
            'insights': [
                'E-commerce penetration at 28% of retail, growing 15% YoY',
                'Omnichannel retailers showing 25% higher conversion rates',
                'Personalization improving customer lifetime value by 20%',
                'Sustainable products representing 31% of consumer purchases'
            ]
        },
        {
            'id': 5,
            'title': 'Workforce & Talent Management 2025',
            'source': 'Deloitte Global',
            'date': 'January 2025',
            'summary': 'Deloitte\'s Global Human Capital Trends report identifies critical workforce challenges and opportunities: (1) Skills gap creating labor shortage with 67% of companies citing inadequate talent; (2) Remote work becoming permanent for 55% of workforce; (3) Upskilling investments averaging $1,500 per employee annually; (4) Diversity initiatives correlating with 22% higher employee retention; (5) Gig economy growing to 27% of workforce; (6) Burnout affecting 48% of employees. Companies prioritizing employee experience, flexible work, and continuous learning gaining 40% better talent acquisition results.',
            'category': 'Workforce & HR',
            'insights': [
                'Skills gap affecting 67% of organizations globally',
                'Remote work sustaining at 55% of workforce post-pandemic',
                'Upskilling investments averaging $1,500 per employee',
                'Diverse teams showing 22% better retention and 35% higher innovation'
            ]
        },
        {
            'id': 6,
            'title': 'Climate Action & Sustainability Report',
            'source': 'Morgan Stanley Research',
            'date': 'March 2025',
            'summary': 'Morgan Stanley analysis of climate investing opportunities and corporate progress: (1) Clean energy investments reaching $1.8T annually; (2) ESG-focused funds outperforming traditional indices by 4.2% over 3 years; (3) Carbon pricing mechanisms expanding to 64% of global GDP; (4) Net-zero commitments now covering 74% of S&P 500; (5) Water scarcity creating $260B annual impact by 2030. Companies achieving sustainability targets seeing 18% premium valuations. Renewable energy sector creating 2.3M new jobs annually.',
            'category': 'Sustainability',
            'insights': [
                'Clean energy investments at $1.8T annually, growing 21%',
                'ESG funds outperforming by 4.2% over 3-year horizon',
                'Carbon pricing covering 64% of global GDP',
                'Renewable sector creating 2.3M jobs annually'
            ]
        },
        {
            'id': 7,
            'title': 'Healthcare Innovation & Digital Health',
            'source': 'JPMorgan Chase Healthcare Research',
            'date': 'February 2025',
            'summary': 'JPMorgan analysis of healthcare sector transformation: (1) Digital health adoption reaching 73% of patients; (2) AI applications in diagnostics improving accuracy by 15-20%; (3) Telehealth capturing 38% of initial consultations; (4) Healthcare spending projected at 18.3% of GDP by 2025; (5) Biotechnology innovations creating $340B market opportunity; (6) Personalized medicine reaching clinical practice at scale. Companies investing in integrated healthcare platforms seeing 33% better patient outcomes and 28% cost reduction.',
            'category': 'Healthcare & Life Sciences',
            'insights': [
                'Digital health adoption at 73% of patient interactions',
                'AI diagnostics improving accuracy by 15-20%',
                'Telehealth commanding 38% of initial consultations',
                'Personalized medicine market expanding at 18% annually'
            ]
        },
        {
            'id': 8,
            'title': '2025 Banking & Financial Services Outlook',
            'source': 'Wells Fargo Securities',
            'date': 'January 2025',
            'summary': 'Wells Fargo research on financial services transformation: (1) Digital banking adoption at 82% with mobile-first becoming standard; (2) Fintech partnerships accelerating, with 58% of banks collaborating; (3) Open banking creating new revenue streams worth $156B; (4) Cryptocurrency integration advancing with 34% of institutions now supporting digital assets; (5) Cybersecurity attacks up 28% targeting financial sector. Banks investing in API infrastructure and cloud migration gaining 3.2x efficiency improvements.',
            'category': 'Banking & Finance',
            'insights': [
                'Digital banking adoption at 82%, mobile-first standard',
                '58% of banks partnering with fintech companies',
                'Open banking generating $156B new revenue opportunities',
                'Cloud-based banking showing 3.2x efficiency gains'
            ]
        }
    ]
    
    return render_template('analysis_reports.html', reports=reports)



@app.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_payment():
    """Initiate Cashfree payment"""
    try:
        package_id = request.form.get('package_id')
        
        packages = {
            '10': {'credits': 10, 'price': 850},
            '30': {'credits': 30, 'price': 2200},
        }
        
        if package_id not in packages:
            return jsonify({'success': False, 'message': 'Invalid package'}), 400
        
        package = packages[package_id]
        order_id = f"IDA_{current_user.id}_{uuid.uuid4().hex[:12]}"
        
        payment = Payment(
            user_id=current_user.id,
            cashfree_order_id=order_id,
            amount=package['price'],
            credits=package['credits'],
            currency='INR'
        )
        db.session.add(payment)
        db.session.commit()
        
        cashfree_api_url = os.getenv('CASHFREE_API_URL', 'https://api.cashfree.com/pg')
        app_id = os.getenv('CASHFREE_APP_ID')
        api_key = os.getenv('CASHFREE_API_KEY')
        
        payload = {
            'order_id': order_id,
            'order_amount': package['price'],
            'order_currency': 'INR',
            'customer_details': {
                'customer_id': f"user_{current_user.id}",
                'customer_email': current_user.email,
                'customer_phone': '9999999999'
            },
            'order_meta': {
                'return_url': request.host_url.rstrip('/') + url_for('payment_success_redirect'),
                'notify_url': request.host_url.rstrip('/') + url_for('payment_webhook')
            },
            'order_note': f'IDA Credits Purchase - {package["credits"]} credits'
        }
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'x-client-id': app_id,
            'x-client-secret': api_key,
            'x-api-version': '2023-08-01'
        }
        
        response = requests.post(
            f'{cashfree_api_url}/orders',
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'payment_session_id' in data:
                # Return checkout URL for redirect
                checkout_url = data.get('url') or f"https://checkout.cashfree.com/pay/{data.get('payment_session_id')}"
                return jsonify({
                    'success': True,
                    'session_id': data['payment_session_id'],
                    'checkout_url': checkout_url,
                    'order_id': order_id
                })
        
        logging.error(f"Cashfree API error: {response.text}")
        return jsonify({'success': False, 'message': 'Failed to initiate payment'}), 500
        
    except Exception as e:
        logging.error(f"Payment initiation error: {e}")
        return jsonify({'success': False, 'message': 'Error initiating payment'}), 500

@app.route('/payment-success')
def payment_success_redirect():
    """Auto-verify and redirect after Cashfree payment success"""
    try:
        # Cashfree appends order_id and order_status to the return_url
        order_id = request.args.get('order_id')
        order_status = request.args.get('order_status', '')
        logging.info(f"Payment success page: order_id={order_id}, cashfree_status={order_status}")
        
        if not order_id:
            flash('Invalid payment response', 'error')
            return redirect(url_for('buy_credits'))
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            flash('Payment record not found', 'error')
            return redirect(url_for('buy_credits'))
        
        credits_already_added = False

        # If Cashfree already tells us it's PAID, add credits immediately server-side
        if order_status == 'PAID' and payment.status != 'COMPLETED':
            user = User.query.get(payment.user_id)
            if user:
                initial_balance = user.credits
                payment.status = 'COMPLETED'
                payment.completed_at = datetime.utcnow()
                user.add_credits(payment.credits)
                db.session.commit()
                db.session.refresh(user)
                credits_already_added = True
                logging.info(f"✓ Credits added on return: order_id={order_id}, user={user.username}, {initial_balance}→{user.credits}")
        elif payment.status == 'COMPLETED':
            credits_already_added = True

        # Render success page — if credits already added, JS will skip straight to success UI
        return render_template('payment_success.html', order_id=order_id, payment=payment,
                               credits_already_added=credits_already_added)
    except Exception as e:
        logging.error(f"Payment success page error: {e}")
        flash('Error processing payment success', 'error')
        return redirect(url_for('buy_credits'))

@app.route('/payment-callback')
def payment_callback():
    """Handle payment callback from Cashfree - both form and API-initiated payments"""
    try:
        order_id = request.args.get('order_id')
        payment_status = request.args.get('order_status')
        
        logging.info(f"Payment callback received: order_id={order_id}, status={payment_status}")
        
        if not order_id:
            logging.error("Payment callback: No order_id provided")
            flash('Invalid payment response', 'error')
            return redirect(url_for('buy_credits'))
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            logging.error(f"Payment callback: Payment record not found for order {order_id}")
            flash('Payment record not found', 'error')
            return redirect(url_for('buy_credits'))
        
        # Verify this payment belongs to the current user (if logged in)
        # If user is not logged in, they will be logged in after payment is verified
        if current_user.is_authenticated and payment.user_id != current_user.id:
            logging.warning(f"Unauthorized payment access attempt: user {current_user.id} trying to access payment for user {payment.user_id}")
            flash('Unauthorized payment access', 'error')
            return redirect(url_for('buy_credits'))
        
        if payment_status == 'PAID':
            # Check if payment was already processed to prevent double-crediting
            if payment.status == 'COMPLETED':
                logging.info(f"Payment {order_id} already processed. Skipping credit addition.")
                # Log the user in if they're not already logged in
                if not current_user.is_authenticated:
                    user = User.query.get(payment.user_id)
                    if user:
                        login_user(user)
                        logging.info(f"User {user.username} logged in for completed payment")
                flash('Payment already processed. Credits were previously added to your account.', 'info')
                return redirect(url_for('index'))
            
            app_id = os.getenv('CASHFREE_APP_ID')
            api_key = os.getenv('CASHFREE_API_KEY')
            cashfree_api_url = os.getenv('CASHFREE_API_URL', 'https://api.cashfree.com/pg')
            
            if not app_id or not api_key:
                logging.error("Cashfree API credentials not configured")
                flash('Payment gateway configuration error', 'error')
                return redirect(url_for('buy_credits'))
            
            headers = {
                'accept': 'application/json',
                'x-client-id': app_id,
                'x-client-secret': api_key,
                'x-api-version': '2023-08-01'
            }
            
            response = requests.get(
                f'{cashfree_api_url}/orders/{order_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('order_status') == 'PAID':
                    user = User.query.get(payment.user_id)
                    if user:
                        # Add credits to user
                        initial_balance = user.credits
                        payment.status = 'COMPLETED'
                        payment.completed_at = datetime.utcnow()
                        user.add_credits(payment.credits)
                        db.session.commit()
                        
                        # Refresh user from database to ensure session is updated
                        db.session.refresh(user)
                        
                        # Log the user in if they're not already logged in
                        if not current_user.is_authenticated:
                            login_user(user)
                            logging.info(f"User {user.username} logged in after successful payment")
                        
                        logging.info(f"✓ Payment COMPLETED: order_id={order_id}, user={user.username}, credits_added={payment.credits}, balance={initial_balance}→{user.credits}")
                        flash(f'Payment successful! {payment.credits} credits added to your account.', 'success')
                        return redirect(url_for('index'))
                    else:
                        logging.error(f"User not found for payment {order_id}")
                        flash('User not found for this payment', 'error')
                        return redirect(url_for('index'))
                else:
                    logging.warning(f"Cashfree order status not PAID: {data.get('order_status')}")
            else:
                logging.error(f"Cashfree API error: {response.status_code} - {response.text}")
        
        # If we get here, payment was not successful
        payment.status = 'FAILED'
        db.session.commit()
        logging.warning(f"Payment marked as FAILED: order_id={order_id}, status={payment_status}")
        flash('Payment failed or was cancelled. Please try again.', 'error')
        return redirect(url_for('buy_credits'))
        
    except Exception as e:
        logging.error(f"Payment callback error: {str(e)}", exc_info=True)
        flash('Error processing payment. Please contact support if problem persists.', 'error')
        return redirect(url_for('buy_credits'))

@app.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """Handle webhook notifications from Cashfree"""
    try:
        data = request.json or {}
        order_id = data.get('order_id')
        order_status = data.get('order_status')
        
        logging.info(f"Webhook received: order_id={order_id}, status={order_status}")
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if payment and order_status == 'PAID' and payment.status == 'PENDING':
            user = User.query.get(payment.user_id)
            if user:
                initial_balance = user.credits
                payment.status = 'COMPLETED'
                payment.completed_at = datetime.utcnow()
                user.add_credits(payment.credits)
                db.session.commit()
                logging.info(f"✓ Webhook COMPLETED: order_id={order_id}, user={user.username}, credits_added={payment.credits}, balance={initial_balance}→{user.credits}")
            else:
                logging.error(f"User not found for payment webhook {order_id}")
                payment.status = 'FAILED'
                db.session.commit()
        elif payment:
            logging.warning(f"Webhook received but payment already processed: order_id={order_id}, current_status={payment.status}")
        else:
            logging.warning(f"Webhook received for unknown payment: order_id={order_id}")
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/payment-page')
@login_required
def payment_page():
    """Display payment page with checkout link"""
    order_id = request.args.get('order_id')
    session_id = request.args.get('session_id')
    
    if not order_id or not session_id:
        flash('Invalid payment parameters', 'error')
        return redirect(url_for('buy_credits'))
    
    payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
    if not payment:
        flash('Payment record not found', 'error')
        return redirect(url_for('buy_credits'))
    
    checkout_url = f"https://checkout.cashfree.com/pay/{session_id}"
    return render_template('simple_payment.html', 
                         order_id=order_id, 
                         amount=payment.amount,
                         credits=payment.credits,
                         checkout_url=checkout_url)

@app.route('/test-payment-complete', methods=['POST'])
@login_required
def test_payment_complete():
    """Complete test payment and add credits"""
    try:
        order_id = request.form.get('order_id')
        
        if not order_id:
            flash('Invalid order ID', 'error')
            return redirect(url_for('buy_credits'))
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            flash('Payment record not found', 'error')
            return redirect(url_for('buy_credits'))
        
        if payment.status != 'PENDING':
            flash('This payment has already been processed', 'error')
            return redirect(url_for('index'))
        
        # Mark payment as completed
        payment.status = 'COMPLETED'
        payment.completed_at = datetime.utcnow()
        
        # Add credits to user
        user = User.query.get(payment.user_id)
        if user:
            user.add_credits(payment.credits)
            db.session.commit()
            
            logging.info(f"Test payment completed for user {user.username}. Credits added: {payment.credits}. New balance: {user.credits}")
            flash(f'Payment successful! {payment.credits} credits have been added to your account.', 'success')
            return redirect(url_for('index'))
        else:
            flash('User not found', 'error')
            return redirect(url_for('buy_credits'))
    
    except Exception as e:
        logging.error(f"Test payment completion error: {e}")
        flash('Error processing payment', 'error')
        return redirect(url_for('buy_credits'))

@app.route('/redirect-to-checkout')
@login_required
def redirect_to_checkout():
    """Show verification page, then redirect to Cashfree hosted checkout page"""
    try:
        order_id = request.args.get('order_id')
        
        if not order_id:
            flash('Invalid order ID', 'error')
            return redirect(url_for('buy_credits'))
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            flash('Payment record not found', 'error')
            return redirect(url_for('buy_credits'))
        
        if payment.user_id != current_user.id:
            flash('Unauthorized payment access', 'error')
            return redirect(url_for('buy_credits'))
        
        # Redirect to Cashfree payment form
        checkout_url = "https://payments.cashfree.com/forms?code=iida"
        logging.info(f"Redirecting user {current_user.username} to Cashfree checkout for order {order_id}")
        return redirect(checkout_url)
    
    except Exception as e:
        logging.error(f"Checkout redirect error: {e}")
        flash('Error accessing checkout', 'error')
        return redirect(url_for('buy_credits'))

@app.route('/verify-payment', methods=['GET', 'POST'])
@login_required
def verify_payment():
    """Show payment verification page"""
    try:
        order_id = request.args.get('order_id') or request.form.get('order_id')
        
        if not order_id:
            flash('Invalid order ID', 'error')
            return redirect(url_for('buy_credits'))
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            flash('Payment record not found', 'error')
            return redirect(url_for('buy_credits'))
        
        if payment.user_id != current_user.id:
            flash('Unauthorized payment access', 'error')
            return redirect(url_for('buy_credits'))
        
        return render_template('payment_verification.html',
                             order_id=order_id,
                             amount=payment.amount,
                             credits=payment.credits)
    
    except Exception as e:
        logging.error(f"Payment verification page error: {e}")
        flash('Error loading payment verification', 'error')
        return redirect(url_for('buy_credits'))

@app.route('/verify-and-complete-payment', methods=['POST'])
@login_required
def verify_and_complete_payment():
    """Verify payment with Cashfree and complete it"""
    try:
        order_id = request.form.get('order_id')
        
        if not order_id:
            flash('Invalid order ID', 'error')
            return redirect(url_for('buy_credits'))
        
        payment = Payment.query.filter_by(cashfree_order_id=order_id).first()
        if not payment:
            flash('Payment record not found', 'error')
            return redirect(url_for('buy_credits'))
        
        if payment.user_id != current_user.id:
            flash('Unauthorized payment access', 'error')
            return redirect(url_for('buy_credits'))
        
        # Check payment status with Cashfree
        app_id = os.getenv('CASHFREE_APP_ID')
        api_key = os.getenv('CASHFREE_API_KEY')
        cashfree_api_url = os.getenv('CASHFREE_API_URL', 'https://api.cashfree.com/pg')
        
        headers = {
            'accept': 'application/json',
            'x-client-id': app_id,
            'x-client-secret': api_key,
            'x-api-version': '2023-08-01'
        }
        
        # Fetch order status from Cashfree
        response = requests.get(
            f'{cashfree_api_url}/orders/{order_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            order_data = response.json()
            order_status = order_data.get('order_status', '')
            
            if order_status == 'PAID':
                # Payment confirmed, update payment record
                if payment.status == 'PENDING':
                    payment.status = 'COMPLETED'
                    payment.completed_at = datetime.utcnow()
                    user = User.query.get(payment.user_id)
                    if user:
                        user.add_credits(payment.credits)
                        db.session.commit()
                        
                        # Refresh user from database to ensure session is updated
                        db.session.refresh(user)
                        
                        logging.info(f"Payment verified and completed for user {user.username}. Credits added: {payment.credits}. New balance: {user.credits}")
                        flash(f'Payment verified! {payment.credits} credits have been added to your account.', 'success')
                        return redirect(url_for('index'))
                else:
                    flash(f'Payment already processed. Status: {payment.status}', 'info')
                    return redirect(url_for('index'))
            else:
                flash(f'Payment not yet completed. Current status: {order_status}', 'warning')
                return redirect(url_for('verify_payment', order_id=order_id))
        else:
            logging.error(f"Failed to fetch payment status from Cashfree: {response.text}")
            flash('Failed to verify payment. Please try again.', 'error')
            return redirect(url_for('verify_payment', order_id=order_id))
            
        return redirect(url_for('index'))
    
    except Exception as e:
        logging.error(f"Payment verification error: {e}")
        flash(f'Error verifying payment: {str(e)}', 'error')
        return redirect(url_for('buy_credits'))

@app.route('/quick-talk')
@login_required
def quick_talk():
    """Quick Talk - Problem solving assistant with Claude AI (costs 3 credits)"""
    # Check if user has enough credits
    if current_user.credits < 3:
        flash('Insufficient credits. You need 3 credits to use Quick Talk. Buy credits to continue.', 'error')
        return redirect(url_for('buy_credits'))
    
    # Deduct 3 credits for this session
    current_user.credits -= 3
    db.session.commit()
    logging.info(f"Quick Talk session started: user={current_user.username}, credits_deducted=3, remaining_credits={current_user.credits}")
    
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    return render_template('quick_talk.html', api_key=api_key)

@app.route('/figma-workspace', methods=['GET', 'POST'])
@login_required
def figma_workspace():
    """Figma Workspace - Locked workspace with Figma iframe (costs 10 credits)"""
    
    # Handle POST request to unlock and deduct credits
    if request.method == 'POST':
        # Check if user has enough credits
        if current_user.credits < 10:
            return jsonify({'success': False, 'error': 'Insufficient credits', 'redirect': '/buy-credits'}), 402
        
        # Deduct 10 credits
        current_user.credits -= 10
        db.session.commit()
        logging.info(f"Figma workspace unlocked: user={current_user.username}, credits_deducted=10, remaining_credits={current_user.credits}")
        
        return jsonify({
            'success': True, 
            'remaining_credits': current_user.credits,
            'message': 'Workspace unlocked successfully'
        })
    
    # Handle GET request - display page
    return render_template('figma_workspace.html')
