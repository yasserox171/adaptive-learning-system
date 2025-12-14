# =============================================================================
# app.py - نظام التعلم التكيفي الكامل
# =============================================================================

import sys
import os
import json
import re
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup

# =============================================================================
# تهيئة التطبيق
# =============================================================================
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adaptive_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '⚠️ يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'warning'

# =============================================================================
# نماذج قاعدة البيانات
# =============================================================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), default='student')
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')
    created_lessons = db.relationship('Lesson', backref='teacher', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    def __repr__(self):
        return f'<User {self.id}: {self.name} ({self.user_type})>'


class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    level_id = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer, default=0)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sections = db.relationship('Section', backref='lesson', lazy=True, 
                               order_by='Section.order', cascade='all, delete-orphan')


class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False, index=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    diagnostics = db.relationship('Diagnostic', backref='section', lazy=True, 
                                  cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='section', lazy=True, 
                                cascade='all, delete-orphan')
    exercises = db.relationship('Exercise', backref='section', lazy=True, 
                                cascade='all, delete-orphan')


class Diagnostic(db.Model):
    __tablename__ = 'diagnostics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='single_choice')
    options = db.Column(db.Text)
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    points = db.Column(db.Integer, default=10)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False, index=True)
    
    def get_options_list(self):
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_correct_answers_list(self):
        if not self.correct_answer:
            return []
        try:
            if self.question_type == 'multiple_choice':
                return json.loads(self.correct_answer)
            else:
                return [self.correct_answer]
        except (json.JSONDecodeError, TypeError):
            return [self.correct_answer]


class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_type = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False, index=True)
    
    exercises = db.relationship('Exercise', backref='reminder', lazy=True, 
                                cascade='all, delete-orphan')


class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    level = db.Column(db.Integer, default=0)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), index=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), index=True)
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text)
    points = db.Column(db.Integer, default=10)


class Result(db.Model):
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False, index=True)
    diagnostic_id = db.Column(db.Integer, db.ForeignKey('diagnostics.id'), index=True)
    is_correct = db.Column(db.Boolean, nullable=False)
    answer = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# =============================================================================
# دوال المساعدة والتحقق
# =============================================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('⚠️ يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        
        if not current_user.is_teacher():
            flash('🚫 هذه الصفحة للمعلمين فقط', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def validate_section_form(data):
    """
    التحقق من صحة بيانات نموذج الفقرة
    """
    errors = []
    
    if not data.get('title', '').strip():
        errors.append('عنوان الفقرة مطلوب')
    
    if not data.get('content', '').strip():
        errors.append('محتوى الفقرة مطلوب')
    
    return errors

def validate_diagnostic_form(data, question_type):
    """
    التحقق من صحة بيانات نموذج الاختبار التشخيصي
    """
    errors = []
    
    if not data.get('question', '').strip():
        errors.append('نص السؤال مطلوب')
    
    if question_type == 'single_choice':
        if not data.get('correct_answer_single'):
            errors.append('الإجابة الصحيحة مطلوبة')
    
    elif question_type == 'multiple_choice':
        has_correct = False
        for key in data:
            if key.startswith('correct') and data[key] == 'on':
                has_correct = True
                break
        if not has_correct:
            errors.append('يجب اختيار إجابة صحيحة واحدة على الأقل')
    
    elif question_type == 'fill_blank':
        if not data.get('correct_answer_fill', '').strip():
            errors.append('الإجابة الصحيحة مطلوبة')
    
    return errors

def calculate_percentage_score(diagnostics, answers):
    """حساب النسبة المئوية للطالب"""
    total_points = 0
    earned_points = 0
    
    for diagnostic in diagnostics:
        total_points += diagnostic.points if diagnostic.points else 10
        
        if str(diagnostic.id) in answers:
            user_answer = answers[str(diagnostic.id)]
            
            if diagnostic.question_type == 'single_choice':
                if user_answer == diagnostic.correct_answer:
                    earned_points += diagnostic.points if diagnostic.points else 10
            elif diagnostic.question_type == 'multiple_choice':
                try:
                    correct_answers = json.loads(diagnostic.correct_answer)
                    user_answers = user_answer if isinstance(user_answer, list) else [user_answer]
                    
                    if set(user_answers) == set(correct_answers):
                        earned_points += diagnostic.points if diagnostic.points else 10
                except:
                    pass
            elif diagnostic.question_type == 'fill_blank':
                correct_answers = [a.strip() for a in diagnostic.correct_answer.split(',')]
                if user_answer.strip() in correct_answers:
                    earned_points += diagnostic.points if diagnostic.points else 10
    
    if total_points == 0:
        return 0
    
    percentage = (earned_points / total_points) * 100
    return round(percentage, 2)

# =============================================================================
# فلاتر Jinja2
# =============================================================================

@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

@app.template_filter('striptags')
def striptags_filter(value):
    if not value:
        return ''
    return re.sub(r'<[^>]*>', '', str(value))

@app.template_filter('safe')
def safe_filter(value):
    return Markup(value)

# =============================================================================
# دوال تحويل النماذج
# =============================================================================

def exercise_to_dict(exercise):
    return {
        'id': exercise.id,
        'title': exercise.title or 'تمرين',
        'content': exercise.content,
        'level': exercise.level,
        'correct_answer': exercise.correct_answer,
        'explanation': exercise.explanation or '',
        'points': exercise.points
    }

def reminder_to_dict(reminder):
    return {
        'id': reminder.id,
        'title': reminder.title or f'تذكير المستوى {reminder.reminder_type}',
        'content': reminder.content,
        'reminder_type': reminder.reminder_type,
        'exercises': [exercise_to_dict(ex) for ex in reminder.exercises]
    }

def diagnostic_to_dict(diagnostic):
    return {
        'id': diagnostic.id,
        'question': diagnostic.question,
        'question_type': diagnostic.question_type,
        'options': diagnostic.get_options_list(),
        'correct_answer': diagnostic.correct_answer,
        'correct_answers_list': diagnostic.get_correct_answers_list(),
        'explanation': diagnostic.explanation or '',
        'points': diagnostic.points or 10
    }

# =============================================================================
# المسارات الرئيسية
# =============================================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'✅ مرحباً بعودتك، {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'student')
        
        if not name or not email or not password:
            flash('⚠️ جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('❌ البريد الإلكتروني مسجل مسبقاً', 'danger')
            return redirect(url_for('register'))
        
        user = User(name=name, email=email, user_type=user_type)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'🎉 تم إنشاء حسابك بنجاح كـ {user_type}', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_teacher():
        lessons = Lesson.query.filter_by(teacher_id=current_user.id).order_by(Lesson.order).all()
        return render_template('teacher_dashboard.html', 
                             lessons=lessons, 
                             teacher=current_user)
    else:
        lessons = Lesson.query.filter_by(is_published=True).order_by(Lesson.order).all()
        return render_template('student_dashboard.html', 
                             lessons=lessons, 
                             student=current_user)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if not lesson.is_published and not current_user.is_teacher():
        flash('⏳ هذا الدرس غير متاح حالياً', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('lesson.html', lesson=lesson)

@app.route('/section/<int:section_id>')
@login_required
def view_section(section_id):
    section = Section.query.get_or_404(section_id)
    
    if not section.lesson.is_published and not current_user.is_teacher():
        flash('⏳ هذا الدرس غير متاح حالياً', 'warning')
        return redirect(url_for('dashboard'))
    
    diagnostics_data = [diagnostic_to_dict(d) for d in section.diagnostics]
    
    main_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 0]
    advanced_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 1]
    basic_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 2]
    
    diagnostic_result = None
    if section.diagnostics:
        diagnostic = section.diagnostics[0]
        diagnostic_result = Result.query.filter_by(
            student_id=current_user.id,
            diagnostic_id=diagnostic.id
        ).first()
    
    return render_template('section.html', 
                         section=section,
                         diagnostics_data=diagnostics_data,
                         main_exercises=main_exercises,
                         advanced_exercises=advanced_exercises,
                         basic_exercises=basic_exercises,
                         diagnostic_result=diagnostic_result)

# =============================================================================
# مسارات المعلمين
# =============================================================================

@app.route('/teacher/lessons')
@login_required
@teacher_required
def teacher_lessons():
    lessons = Lesson.query.filter_by(teacher_id=current_user.id)\
               .order_by(Lesson.order.desc()).all()
    return render_template('teacher/lessons.html', lessons=lessons)

@app.route('/teacher/lesson/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_lesson():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level_id = request.form.get('level_id', 1, type=int)
        
        if not title:
            flash('⚠️ عنوان الدرس مطلوب', 'warning')
            return redirect(url_for('create_lesson'))
        
        next_order = Lesson.query.filter_by(teacher_id=current_user.id).count() + 1
        
        lesson = Lesson(
            title=title,
            description=description,
            level_id=level_id,
            teacher_id=current_user.id,
            order=next_order
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash('✅ تم إنشاء الدرس بنجاح', 'success')
        return redirect(url_for('edit_lesson', lesson_id=lesson.id))
    
    return render_template('teacher/create_lesson.html')

@app.route('/teacher/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لتعديل هذا الدرس', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        lesson.title = request.form.get('title', '').strip()
        lesson.description = request.form.get('description', '').strip()
        lesson.level_id = request.form.get('level_id', 1, type=int)
        lesson.order = request.form.get('order', 0, type=int)
        lesson.is_published = 'is_published' in request.form
        
        db.session.commit()
        flash('✅ تم تحديث الدرس بنجاح', 'success')
        return redirect(url_for('edit_lesson', lesson_id=lesson.id))
    
    return render_template('teacher/edit_lesson.html', lesson=lesson)

@app.route('/teacher/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})
    
    db.session.delete(lesson)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف الدرس بنجاح'})

@app.route('/teacher/lesson/<int:lesson_id>/section/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_section(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لإضافة فقرات لهذا الدرس', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('⚠️ جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('create_section', lesson_id=lesson_id))
        
        next_order = len(lesson.sections) + 1
        
        section = Section(
            title=title,
            content=content,
            lesson_id=lesson_id,
            order=next_order
        )
        
        db.session.add(section)
        db.session.commit()
        
        flash('✅ تم إنشاء الفقرة بنجاح', 'success')
        return redirect(url_for('edit_lesson', lesson_id=lesson_id))
    
    return render_template('teacher/create_section.html', lesson=lesson)

@app.route('/teacher/section/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_section(section_id):
    """
    ========================================================================
    تعديل فقرة (Edit Section)
    ========================================================================
    """
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لتعديل هذه الفقرة', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        # التحقق من نوع النموذج
        form_type = request.form.get('form_type')
        
        if form_type == 'new_diagnostic':
            # هذا من Modal إضافة سؤال جديد
            return handle_new_diagnostic(section_id)
        
        # هذا من النموذج الرئيسي لتعديل الفقرة
        errors = validate_section_form(request.form)
        
        if errors:
            for error in errors:
                flash(f'⚠️ {error}', 'warning')
        else:
            section.title = request.form.get('title', '').strip()
            section.content = request.form.get('content', '').strip()
            section.order = request.form.get('order', 0, type=int)
            
            db.session.commit()
            flash('✅ تم تحديث الفقرة بنجاح', 'success')
        
        return redirect(url_for('edit_section', section_id=section.id))
    
    return render_template('teacher/edit_section.html', 
                         section=section, 
                         lesson=lesson)

def handle_new_diagnostic(section_id):
    """معالجة إضافة سؤال تشخيصي جديد"""
    section = Section.query.get_or_404(section_id)
    
    question_type = request.form.get('question_type', 'single_choice')
    errors = validate_diagnostic_form(request.form, question_type)
    
    if errors:
        for error in errors:
            flash(f'⚠️ {error}', 'warning')
        return redirect(url_for('edit_section', section_id=section_id))
    
    try:
        # معالجة حسب نوع السؤال
        question = request.form.get('question', '').strip()
        explanation = request.form.get('explanation', '').strip()
        points = request.form.get('points', 10, type=int)
        
        if question_type == 'single_choice':
            # جمع الخيارات
            options = []
            for i in range(1, 7):  # حتى 6 خيارات
                option = request.form.get(f'option{i}', '').strip()
                if option:
                    options.append(option)
            
            correct_answer = request.form.get('correct_answer_single', '').strip()
            
            if not correct_answer or correct_answer not in options:
                flash('⚠️ الإجابة الصحيحة غير صالحة', 'warning')
                return redirect(url_for('edit_section', section_id=section_id))
            
            diagnostic = Diagnostic(
                question=question,
                question_type=question_type,
                options=json.dumps(options),
                correct_answer=correct_answer,
                explanation=explanation,
                points=points,
                section_id=section_id
            )
            
        elif question_type == 'multiple_choice':
            # جمع الخيارات والإجابات الصحيحة
            options = []
            correct_answers = []
            
            for i in range(1, 7):
                option = request.form.get(f'option{i}', '').strip()
                if option:
                    options.append(option)
                    # التحقق إذا كان هذا الخيار صحيحاً
                    is_correct = request.form.get(f'correct{i}', 'off') == 'on'
                    if is_correct:
                        correct_answers.append(option)
            
            if not correct_answers:
                flash('⚠️ يجب اختيار إجابة صحيحة واحدة على الأقل', 'warning')
                return redirect(url_for('edit_section', section_id=section_id))
            
            diagnostic = Diagnostic(
                question=question,
                question_type=question_type,
                options=json.dumps(options),
                correct_answer=json.dumps(correct_answers),
                explanation=explanation,
                points=points,
                section_id=section_id
            )
            
        elif question_type == 'fill_blank':
            correct_answer = request.form.get('correct_answer_fill', '').strip()
            
            diagnostic = Diagnostic(
                question=question,
                question_type=question_type,
                options=json.dumps([]),  # لا توجد خيارات
                correct_answer=correct_answer,
                explanation=explanation,
                points=points,
                section_id=section_id
            )
        
        else:
            flash('❌ نوع السؤال غير صالح', 'danger')
            return redirect(url_for('edit_section', section_id=section_id))
        
        db.session.add(diagnostic)
        db.session.commit()
        
        flash('✅ تم إضافة السؤال التشخيصي بنجاح', 'success')
        
    except Exception as e:
        flash(f'❌ حدث خطأ أثناء حفظ السؤال: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('edit_section', section_id=section_id))

@app.route('/teacher/section/<int:section_id>/diagnostic/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_diagnostic(section_id):
    """إنشاء اختبار تشخيصي (الطريقة القديمة - تحويل إلى edit_section)"""
    section = Section.query.get_or_404(section_id)
    return redirect(url_for('edit_section', section_id=section_id))

@app.route('/teacher/section/<int:section_id>/reminder/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_reminder(section_id):
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لإضافة تذكير', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        reminder_type = request.form.get('reminder_type', type=int)
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('⚠️ محتوى التذكير مطلوب', 'warning')
            return redirect(url_for('create_reminder', section_id=section_id))
        
        reminder = Reminder(
            reminder_type=reminder_type,
            title=title,
            content=content,
            section_id=section_id
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        flash('✅ تم إنشاء التذكير بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section_id))
    
    return render_template('teacher/create_reminder.html', section=section)

@app.route('/teacher/section/<int:section_id>/exercise/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_exercise(section_id):
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لإضافة تمرين', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        level = request.form.get('level', type=int)
        correct_answer = request.form.get('correct_answer', '').strip()
        explanation = request.form.get('explanation', '').strip()
        points = request.form.get('points', 10, type=int)
        
        if not content or not correct_answer:
            flash('⚠️ نص التمرين والإجابة الصحيحة مطلوبان', 'warning')
            return redirect(url_for('create_exercise', section_id=section_id))
        
        exercise = Exercise(
            title=title,
            content=content,
            level=level,
            section_id=section_id,
            correct_answer=correct_answer,
            explanation=explanation,
            points=points
        )
        
        db.session.add(exercise)
        db.session.commit()
        
        flash('✅ تم إنشاء التمرين بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section_id))
    
    return render_template('teacher/create_exercise.html', section=section)

@app.route('/teacher/statistics')
@login_required
@teacher_required
def teacher_statistics():
    total_lessons = Lesson.query.filter_by(teacher_id=current_user.id).count()
    published_lessons = Lesson.query.filter_by(teacher_id=current_user.id, 
                                              is_published=True).count()
    total_students = User.query.filter_by(user_type='student').count()
    
    return render_template('teacher/statistics.html',
                         total_lessons=total_lessons,
                         published_lessons=published_lessons,
                         total_students=total_students)

# =============================================================================
# مسارات الحذف
# =============================================================================

@app.route('/teacher/exercise/<int:exercise_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    section = exercise.section
    
    if section.lesson.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})
    
    db.session.delete(exercise)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف التمرين بنجاح'})

@app.route('/teacher/diagnostic/<int:diagnostic_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_diagnostic(diagnostic_id):
    diagnostic = Diagnostic.query.get_or_404(diagnostic_id)
    section = diagnostic.section
    
    if section.lesson.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})
    
    db.session.delete(diagnostic)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف الاختبار التشخيصي بنجاح'})

@app.route('/teacher/reminder/<int:reminder_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    section = reminder.section
    
    if section.lesson.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})
    
    db.session.delete(reminder)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف التذكير بنجاح'})

@app.route('/teacher/section/<int:section_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})
    
    db.session.delete(section)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف الفقرة بنجاح'})

# =============================================================================
# واجهات API
# =============================================================================

@app.route('/api/diagnostic/<int:diagnostic_id>', methods=['POST'])
@login_required
def submit_diagnostic(diagnostic_id):
    """تقديم إجابة الاختبار التشخيصي مع حساب النسبة المئوية"""
    diagnostic = Diagnostic.query.get_or_404(diagnostic_id)
    data = request.get_json()
    
    if not data or 'answer' not in data:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'}), 400
    
    user_answer = data['answer']
    is_correct = False
    score = 0
    
    # التحقق من الإجابة حسب نوع السؤال
    if diagnostic.question_type == 'single_choice':
        is_correct = user_answer == diagnostic.correct_answer
        score = diagnostic.points if is_correct else 0
        
    elif diagnostic.question_type == 'multiple_choice':
        try:
            correct_answers = json.loads(diagnostic.correct_answer)
            user_answers = user_answer if isinstance(user_answer, list) else [user_answer]
            
            is_correct = set(user_answers) == set(correct_answers)
            score = diagnostic.points if is_correct else 0
            
        except (json.JSONDecodeError, TypeError):
            is_correct = False
            score = 0
            
    elif diagnostic.question_type == 'fill_blank':
        correct_answers = [a.strip() for a in diagnostic.correct_answer.split(',')]
        is_correct = user_answer.strip() in correct_answers
        score = diagnostic.points if is_correct else 0
    
    # حفظ النتيجة
    result = Result(
        student_id=current_user.id,
        diagnostic_id=diagnostic_id,
        is_correct=is_correct,
        answer=str(user_answer),
        score=score
    )
    
    db.session.add(result)
    db.session.commit()
    
    # حساب النسبة المئوية لجميع الأسئلة في الفقرة
    section = diagnostic.section
    all_results = Result.query.filter_by(
        student_id=current_user.id,
        diagnostic_id__in=[d.id for d in section.diagnostics]
    ).all()
    
    total_possible = sum(d.points if d.points else 10 for d in section.diagnostics)
    total_earned = sum(r.score for r in all_results)
    percentage = (total_earned / total_possible * 100) if total_possible > 0 else 0
    
    # تحديد المستوى بناءً على النسبة المئوية
    level = 1 if percentage >= 80 else 2
    
    return jsonify({
        'success': True,
        'correct': is_correct,
        'score': score,
        'percentage': round(percentage, 2),
        'level': level,
        'question_type': diagnostic.question_type,
        'explanation': diagnostic.explanation or '',
        'correct_answers': diagnostic.get_correct_answers_list(),
        'total_questions': len(section.diagnostics),
        'total_score': total_earned,
        'max_score': total_possible
    })

@app.route('/api/exercise/<int:exercise_id>', methods=['POST'])
@login_required
def submit_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    data = request.get_json()
    
    if not data or 'answer' not in data:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'}), 400
    
    is_correct = data['answer'] == exercise.correct_answer
    score = exercise.points if is_correct else 0
    
    result = Result(
        student_id=current_user.id,
        exercise_id=exercise_id,
        is_correct=is_correct,
        answer=data['answer'],
        score=score
    )
    
    db.session.add(result)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'correct': is_correct,
        'score': score,
        'explanation': exercise.explanation or ''
    })

@app.route('/api/section/<int:section_id>/reminders/<int:level>')
@login_required
def get_reminders(section_id, level):
    reminders = Reminder.query.filter_by(
        section_id=section_id,
        reminder_type=level
    ).all()
    
    reminders_data = [reminder_to_dict(reminder) for reminder in reminders]
    
    return jsonify(reminders_data)

@app.route('/api/section/<int:section_id>/exercises/<int:level>')
@login_required
def get_exercises(section_id, level):
    exercises = Exercise.query.filter_by(
        section_id=section_id,
        level=level
    ).all()
    
    exercises_data = [exercise_to_dict(exercise) for exercise in exercises]
    
    return jsonify(exercises_data)

# =============================================================================
# تهيئة قاعدة البيانات
# =============================================================================

# =============================================================================
# تهيئة قاعدة البيانات - نسخة محدثة
# =============================================================================

def init_database():
    """تهيئة قاعدة البيانات وإنشاء بيانات تجريبية"""
    print("\n" + "=" * 60)
    print("🗃️  جارٍ تهيئة قاعدة البيانات...")
    print("=" * 60)
    
    with app.app_context():
        # 1. إنشاء جميع الجداول (سيتم إنشاء الأعمدة الجديدة تلقائياً)
        db.create_all()
        print("✅ تم إنشاء/تحديث جداول قاعدة البيانات")
        
        # 2. التحقق من وجود عمود points في جدول diagnostics
        try:
            # محاولة استعلام للتأكد من وجود العمود
            test_diag = Diagnostic.query.first()
            print("✅ جدول التشخيصات يحتوي على عمود النقاط")
        except Exception as e:
            print(f"⚠️ تحذير: {e}")
            print("🔄 جارٍ تحديث جدول التشخيصات...")
            
            # إذا فشل الاستعلام، نحتاج إلى تحديث الجدول يدوياً
            try:
                # هذا سيعيد إنشاء الجدول
                db.drop_all()
                db.create_all()
                print("✅ تم إعادة إنشاء جميع الجداول")
            except Exception as e2:
                print(f"❌ خطأ في إعادة إنشاء الجداول: {e2}")
        
        # 3. التحقق من وجود المعلم الرئيسي
        teacher = User.query.filter_by(email='teacher@example.com').first()
        if not teacher:
            teacher = User(
                name='المعلم الإداري',
                email='teacher@example.com',
                user_type='teacher'
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            db.session.commit()
            print("✅ تم إنشاء المعلم الرئيسي")
        else:
            print("📌 المعلم الرئيسي موجود مسبقاً")
        
        # 4. التحقق من وجود درس تجريبي
        lesson = Lesson.query.filter_by(title='مقدمة في الرياضيات').first()
        if not lesson:
            lesson = Lesson(
                title='مقدمة في الرياضيات',
                description='تعلم أساسيات العمليات الحسابية',
                level_id=1,
                order=1,
                teacher_id=teacher.id,
                is_published=True
            )
            db.session.add(lesson)
            db.session.commit()
            print("✅ تم إنشاء درس تجريبي")
        else:
            print("📌 الدرس التجريبي موجود مسبقاً")
        
        # 5. التحقق من وجود فقرة تجريبية
        section = Section.query.filter_by(title='الجمع والطرح').first()
        if not section:
            if lesson and lesson.id:
                section = Section(
                    title='الجمع والطرح',
                    content='<h3>مرحباً بك في درس الرياضيات</h3><p>سنتعلم معاً أساسيات الجمع والطرح.</p>',
                    lesson_id=lesson.id,
                    order=1
                )
                db.session.add(section)
                db.session.commit()
                print("✅ تم إنشاء فقرة تجريبية")
        else:
            print("📌 الفقرة التجريبية موجودة مسبقاً")
        
        # 6. التحقق من وجود اختبار تشخيصي تجريبي (بعد التأكد من وجود section)
        if section and section.id:
            diagnostic = Diagnostic.query.filter_by(question='ما هو ناتج 5 + 3؟').first()
            if not diagnostic:
                diagnostic = Diagnostic(
                    question='ما هو ناتج 5 + 3؟',
                    question_type='single_choice',
                    options=json.dumps(['6', '7', '8', '9']),
                    correct_answer='8',
                    explanation='5 + 3 = 8',
                    points=10,  # إضافة النقاط
                    section_id=section.id
                )
                db.session.add(diagnostic)
                print("✅ تم إنشاء اختبار تشخيصي تجريبي")
            else:
                print("📌 الاختبار التشخيصي التجريبي موجود مسبقاً")
                
                # تحديث الاختبار الحالي لإضافة النقاط إذا لم تكن موجودة
                if not diagnostic.points:
                    diagnostic.points = 10
                    db.session.commit()
                    print("✅ تم تحديث الاختبار التشخيصي بإضافة النقاط")
        
        # 7. التحقق من وجود تذكيرات تجريبية
        if section and section.id:
            reminder1 = Reminder.query.filter_by(
                section_id=section.id, 
                reminder_type=1
            ).first()
            
            if not reminder1:
                reminder1 = Reminder(
                    reminder_type=1,
                    title='مراجعة سريعة للجمع',
                    content='الجمع هو عملية تجميع كميتين أو أكثر للحصول على كمية أكبر.',
                    section_id=section.id
                )
                db.session.add(reminder1)
                print("✅ تم إنشاء تذكير مستوى متقدم")
            
            reminder2 = Reminder.query.filter_by(
                section_id=section.id, 
                reminder_type=2
            ).first()
            
            if not reminder2:
                reminder2 = Reminder(
                    reminder_type=2,
                    title='شرح مفصل للجمع',
                    content='لتعلم الجمع: ابدأ بالعدد الأول، ثم أضف العدد الثاني عداً.',
                    section_id=section.id
                )
                db.session.add(reminder2)
                print("✅ تم إنشاء تذكير مستوى أساسي")
        
        # 8. التحقق من وجود تمارين تجريبية
        if section and section.id:
            exercises_count = Exercise.query.filter_by(section_id=section.id).count()
            if exercises_count == 0:
                exercises = [
                    Exercise(
                        title='تمرين أساسي',
                        content='ما هو ناتج 4 + 2؟',
                        level=0,
                        section_id=section.id,
                        correct_answer='6',
                        explanation='4 + 2 = 6',
                        points=10
                    ),
                    Exercise(
                        title='تمرين متقدم',
                        content='ما هو ناتج 12 + 15؟',
                        level=1,
                        section_id=section.id,
                        correct_answer='27',
                        explanation='12 + 15 = 27',
                        points=10
                    ),
                    Exercise(
                        title='تمرين علاجي',
                        content='ما هو ناتج 1 + 1؟',
                        level=2,
                        section_id=section.id,
                        correct_answer='2',
                        explanation='1 + 1 = 2',
                        points=10
                    )
                ]
                
                for exercise in exercises:
                    db.session.add(exercise)
                
                print("✅ تم إنشاء تمارين تجريبية")
        
        try:
            db.session.commit()
            print("✅ تم حفظ جميع البيانات في قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في حفظ البيانات: {e}")
            db.session.rollback()
        
        # 9. عرض ملخص قاعدة البيانات
        print("\n📊 ملخص قاعدة البيانات:")
        print(f"   👨‍🏫 المعلمون: {User.query.filter_by(user_type='teacher').count()}")
        print(f"   👨‍🎓 الطلاب: {User.query.filter_by(user_type='student').count()}")
        print(f"   📚 الدروس: {Lesson.query.count()}")
        print(f"   📝 الفقرات: {Section.query.count()}")
        print(f"   ❓ الاختبارات التشخيصية: {Diagnostic.query.count()}")
        print(f"   💡 التذكيرات: {Reminder.query.count()}")
        print(f"   📝 التمارين: {Exercise.query.count()}")
        
        print("\n🎉 قاعدة البيانات جاهزة للاستخدام!")
# =============================================================================
# نقطة الدخول الرئيسية
# =============================================================================

if __name__ == '__main__':
    # إنشاء مجلد التحميلات إذا لم يكن موجوداً
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print(f"📁 تم إنشاء مجلد التحميلات: {app.config['UPLOAD_FOLDER']}")
    
    # تهيئة قاعدة البيانات
    init_database()
    
    # معلومات التشغيل
    print("\n" + "=" * 70)
    print("🚀 بدء تشغيل خادم التطوير")
    print("=" * 70)
    print("🌐 روابط الوصول:")
    print(f"   📍 http://localhost:5000")
    print(f"   📍 http://127.0.0.1:5000")
    
    print("\n👤 حسابات تجريبية:")
    print("   👨‍🏫 المعلم: teacher@example.com / teacher123")
    print("   👨‍🎓 الطالب: أنشئ حساباً جديداً")
    
    print("\n💡 نصائح:")
    print("   1. اضغط Ctrl+C لإيقاف الخادم")
    print("   2. افتح المتصفح واذهب إلى http://localhost:5000")
    
    print("\n" + "=" * 70)
    
    # تشغيل التطبيق
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {e}")