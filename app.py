"""
app.py - نظام التعلم التكيفي الكامل
إصدار متوافق مع جميع المسارات
"""

import sys
import os

# طباعة معلومات النظام
print("=" * 60)
print("🚀 بدء تشغيل نظام التعلم التكيفي")
print("=" * 60)
print(f"📌 Python: {sys.version}")
print(f"📁 المجلد: {os.getcwd()}")

try:
    # استيراد المكتبات
    print("📦 جارٍ استيراد المكتبات...")
    
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
    print("✅ Flask")
    
    from flask_sqlalchemy import SQLAlchemy
    print("✅ Flask-SQLAlchemy")
    
    from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
    print("✅ Flask-Login")
    
    from datetime import datetime
    import json
    from werkzeug.security import generate_password_hash, check_password_hash
    
    print("✅ جميع المكتبات تم استيرادها بنجاح!")
    
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    print("\n🔧 الحل: قم بتثبيت المكتبات المطلوبة:")
    print("pip install Flask==2.3.3 Werkzeug==2.3.7 Flask-Login==0.6.3 Flask-SQLAlchemy==3.0.5")
    sys.exit(1)

# إنشاء تطبيق Flask
app = Flask(__name__)

# إعدادات التطبيق
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adaptive_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة الإضافات
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'info'

# ===================== نماذج قاعدة البيانات =====================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), default='student')  # 'student' أو 'teacher'
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    results = db.relationship('Result', backref='student', lazy=True)
    created_lessons = db.relationship('Lesson', backref='teacher', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name} ({self.user_type})>'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    level_id = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer, default=0)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    sections = db.relationship('Section', backref='lesson', lazy=True, order_by='Section.order')
    
    def __repr__(self):
        return f'<Lesson {self.title}>'

class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    diagnostics = db.relationship('Diagnostic', backref='section', lazy=True)
    reminders = db.relationship('Reminder', backref='section', lazy=True)
    exercises = db.relationship('Exercise', backref='section', lazy=True)
    
    def __repr__(self):
        return f'<Section {self.title}>'

class Diagnostic(db.Model):
    __tablename__ = 'diagnostics'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)  # JSON string
    correct_answer = db.Column(db.String(10), nullable=False)
    explanation = db.Column(db.Text)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    
    def __repr__(self):
        return f'<Diagnostic {self.id}>'

class Reminder(db.Model):
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True)
    reminder_type = db.Column(db.Integer, nullable=False)  # 1 أو 2
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    
    # العلاقات
    exercises = db.relationship('Exercise', backref='reminder', lazy=True)
    
    def __repr__(self):
        return f'<Reminder {self.title} (Type: {self.reminder_type})>'

class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    level = db.Column(db.Integer, default=0)  # 0 = رئيسي، 1 = متقدم، 2 = أساسي
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'))
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'))
    correct_answer = db.Column(db.String(500))
    explanation = db.Column(db.Text)
    points = db.Column(db.Integer, default=10)
    
    def __repr__(self):
        return f'<Exercise {self.title} (Level: {self.level})>'

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    diagnostic_id = db.Column(db.Integer, db.ForeignKey('diagnostics.id'))
    is_correct = db.Column(db.Boolean, nullable=False)
    answer = db.Column(db.Text)
    score = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Result User:{self.student_id} Exercise:{self.exercise_id} Correct:{self.is_correct}>'
# ===================== دوال المساعدة =====================
# ===================== فلاتر Jinja2 المخصصة =====================

# تعريف فلتر from_json لتحويل JSON string إلى Python object
@app.template_filter('from_json')
def from_json_filter(value):
    """تحويل JSON string إلى Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

# فلترات إضافية مفيدة
@app.template_filter('striptags')
def striptags_filter(value):
    """إزالة الوسوم HTML من النص"""
    if not value:
        return ''
    import re
    return re.sub(r'<[^>]*>', '', str(value))

@app.template_filter('safe')
def safe_filter(value):
    """علامة النص كآمن للعرض (لا يحتاج escaping)"""
    from markupsafe import Markup
    return Markup(value)


def exercise_to_dict(exercise):
    """تحويل كائن Exercise إلى dictionary"""
    return {
        'id': exercise.id,
        'title': exercise.title,
        'content': exercise.content,
        'level': exercise.level,
        'correct_answer': exercise.correct_answer,
        'explanation': exercise.explanation,
        'points': exercise.points
    }

def reminder_to_dict(reminder):
    """تحويل كائن Reminder إلى dictionary"""
    return {
        'id': reminder.id,
        'title': reminder.title,
        'content': reminder.content,
        'reminder_type': reminder.reminder_type,
        'exercises': [exercise_to_dict(ex) for ex in reminder.exercises]
    }

def diagnostic_to_dict(diagnostic):
    """تحويل كائن Diagnostic إلى dictionary"""
    try:
        options = json.loads(diagnostic.options) if diagnostic.options else []
    except:
        options = []
    
    return {
        'id': diagnostic.id,
        'question': diagnostic.question,
        'options': options,
        'correct_answer': diagnostic.correct_answer,
        'explanation': diagnostic.explanation
    }
@login_manager.user_loader
def load_user(user_id):
    """تحميل المستخدم من قاعدة البيانات"""
    return User.query.get(int(user_id))

def teacher_required(f):
    """ديكوراتور للتحقق من أن المستخدم معلم"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        
        if current_user.user_type != 'teacher':
            flash('هذه الصفحة للمعلمين فقط', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function

# ===================== مسارات الصفحات =====================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة التسجيل"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'student')
        
        # التحقق من عدم وجود المستخدم مسبقاً
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مسجل مسبقاً', 'danger')
            return redirect(url_for('register'))
        
        # إنشاء المستخدم
        user = User(name=name, email=email, user_type=user_type)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'تم إنشاء الحساب بنجاح كـ {user_type}', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم"""
    if current_user.user_type == 'teacher':
        lessons = Lesson.query.filter_by(teacher_id=current_user.id).order_by(Lesson.order).all()
        return render_template('teacher_dashboard.html', lessons=lessons, teacher=current_user)
    else:
        lessons = Lesson.query.filter_by(is_published=True).order_by(Lesson.order).all()
        return render_template('student_dashboard.html', lessons=lessons, student=current_user)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    """عرض الدرس"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # التحقق من صلاحيات الوصول
    if not lesson.is_published and current_user.user_type != 'teacher':
        flash('هذا الدرس غير متاح حالياً', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('lesson.html', lesson=lesson)

@app.route('/section/<int:section_id>')
@login_required
def view_section(section_id):
    """عرض الفقرة"""
    section = Section.query.get_or_404(section_id)
    
    # التحقق من صلاحيات الوصول
    if not section.lesson.is_published and current_user.user_type != 'teacher':
        flash('هذا الدرس غير متاح حالياً', 'warning')
        return redirect(url_for('dashboard'))
    
    # تحويل البيانات إلى dictionaries قابلة للتسلسل
    diagnostics_data = [diagnostic_to_dict(d) for d in section.diagnostics]
    
    # تجميع التمارين حسب المستوى
    main_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 0]
    advanced_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 1]
    basic_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 2]
    
    # التحقق من وجود نتائج تشخيص سابقة
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

# ===================== مسارات المعلمين =====================

@app.route('/teacher/lessons')
@login_required
@teacher_required
def teacher_lessons():
    """صفحة إدارة الدروس للمعلم"""
    lessons = Lesson.query.filter_by(teacher_id=current_user.id).order_by(Lesson.order.desc()).all()
    return render_template('teacher/lessons.html', lessons=lessons)

@app.route('/teacher/lesson/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_lesson():
    """إنشاء درس جديد"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        level_id = request.form.get('level_id', 1, type=int)
        
        lesson = Lesson(
            title=title,
            description=description,
            level_id=level_id,
            teacher_id=current_user.id,
            order=Lesson.query.filter_by(teacher_id=current_user.id).count() + 1
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash('تم إنشاء الدرس بنجاح', 'success')
        return redirect(url_for('edit_lesson', lesson_id=lesson.id))
    
    return render_template('teacher/create_lesson.html')

@app.route('/teacher/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_lesson(lesson_id):
    """تعديل درس"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # التحقق من أن المعلم هو منشئ الدرس
    if lesson.teacher_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا الدرس', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        lesson.title = request.form.get('title')
        lesson.description = request.form.get('description')
        lesson.level_id = request.form.get('level_id', 1, type=int)
        lesson.order = request.form.get('order', 0, type=int)
        lesson.is_published = 'is_published' in request.form
        
        db.session.commit()
        flash('تم تحديث الدرس بنجاح', 'success')
        return redirect(url_for('edit_lesson', lesson_id=lesson.id))
    
    return render_template('teacher/edit_lesson.html', lesson=lesson)

@app.route('/teacher/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    """حذف درس"""
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
    """إنشاء فقرة جديدة"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != current_user.id:
        flash('ليس لديك صلاحية لإضافة فقرات لهذا الدرس', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        section = Section(
            title=title,
            content=content,
            lesson_id=lesson_id,
            order=len(lesson.sections) + 1
        )
        
        db.session.add(section)
        db.session.commit()
        
        flash('تم إنشاء الفقرة بنجاح', 'success')
        return redirect(url_for('edit_lesson', lesson_id=lesson_id))
    
    return render_template('teacher/create_section.html', lesson=lesson)

@app.route('/teacher/section/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_section(section_id):
    """تعديل فقرة"""
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذه الفقرة', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        section.title = request.form.get('title')
        section.content = request.form.get('content')
        section.order = request.form.get('order', 0, type=int)
        
        db.session.commit()
        flash('تم تحديث الفقرة بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section.id))
    
    return render_template('teacher/edit_section.html', section=section, lesson=lesson)

@app.route('/teacher/section/<int:section_id>/diagnostic/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_diagnostic(section_id):
    """إنشاء اختبار تشخيصي"""
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('ليس لديك صلاحية لإضافة اختبار تشخيصي', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        question = request.form.get('question')
        options = json.dumps([
            request.form.get('option1'),
            request.form.get('option2'),
            request.form.get('option3'),
            request.form.get('option4')
        ])
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        
        diagnostic = Diagnostic(
            question=question,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            section_id=section_id
        )
        
        db.session.add(diagnostic)
        db.session.commit()
        
        flash('تم إنشاء الاختبار التشخيصي بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section_id))
    
    return render_template('teacher/create_diagnostic.html', section=section)

@app.route('/teacher/section/<int:section_id>/reminder/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_reminder(section_id):
    """إنشاء تذكير"""
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('ليس لديك صلاحية لإضافة تذكير', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        reminder_type = request.form.get('reminder_type', type=int)
        title = request.form.get('title')
        content = request.form.get('content')
        
        reminder = Reminder(
            reminder_type=reminder_type,
            title=title,
            content=content,
            section_id=section_id
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        flash('تم إنشاء التذكير بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section_id))
    
    return render_template('teacher/create_reminder.html', section=section)

@app.route('/teacher/section/<int:section_id>/exercise/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_exercise(section_id):
    """إنشاء تمرين"""
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('ليس لديك صلاحية لإضافة تمرين', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        level = request.form.get('level', type=int)
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        points = request.form.get('points', 10, type=int)
        
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
        
        flash('تم إنشاء التمرين بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section_id))
    
    return render_template('teacher/create_exercise.html', section=section)

@app.route('/teacher/statistics')
@login_required
@teacher_required
def teacher_statistics():
    """صفحة الإحصائيات للمعلم"""
    total_lessons = Lesson.query.filter_by(teacher_id=current_user.id).count()
    published_lessons = Lesson.query.filter_by(teacher_id=current_user.id, is_published=True).count()
    total_students = User.query.filter_by(user_type='student').count()
    
    return render_template('teacher/statistics.html',
                         total_lessons=total_lessons,
                         published_lessons=published_lessons,
                         total_students=total_students)

# مسارات حذف العناصر
@app.route('/teacher/exercise/<int:exercise_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_exercise(exercise_id):
    """حذف تمرين"""
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
    """حذف اختبار تشخيصي"""
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
    """حذف تذكير"""
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
    """حذف فقرة"""
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})
    
    db.session.delete(section)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف الفقرة بنجاح'})

# ===================== مسارات API =====================

@app.route('/api/diagnostic/<int:diagnostic_id>', methods=['POST'])
@login_required
def submit_diagnostic(diagnostic_id):
    """تقديم إجابة الاختبار التشخيصي"""
    diagnostic = Diagnostic.query.get_or_404(diagnostic_id)
    data = request.json
    
    is_correct = data.get('answer') == diagnostic.correct_answer
    score = 10 if is_correct else 0
    
    result = Result(
        student_id=current_user.id,
        diagnostic_id=diagnostic_id,
        is_correct=is_correct,
        answer=data.get('answer'),
        score=score
    )
    
    db.session.add(result)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'correct': is_correct,
        'score': score,
        'level': 1 if score >= 10 else 2,
        'explanation': diagnostic.explanation
    })

@app.route('/api/exercise/<int:exercise_id>', methods=['POST'])
@login_required
def submit_exercise(exercise_id):
    """تقديم إجابة التمرين"""
    exercise = Exercise.query.get_or_404(exercise_id)
    data = request.json
    
    is_correct = data.get('answer') == exercise.correct_answer
    score = exercise.points if is_correct else 0
    
    result = Result(
        student_id=current_user.id,
        exercise_id=exercise_id,
        is_correct=is_correct,
        answer=data.get('answer'),
        score=score
    )
    
    db.session.add(result)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'correct': is_correct,
        'score': score,
        'explanation': exercise.explanation
    })
@app.route('/api/section/<int:section_id>/reminders/<int:level>')
@login_required
def get_reminders(section_id, level):
    """جلب التذكيرات حسب المستوى"""
    reminders = Reminder.query.filter_by(
        section_id=section_id,
        reminder_type=level
    ).all()
    
    reminders_data = []
    for reminder in reminders:
        reminders_data.append({
            'id': reminder.id,
            'title': reminder.title,
            'content': reminder.content,
            'exercises': [exercise_to_dict(ex) for ex in reminder.exercises]
        })
    
    return jsonify(reminders_data)

@app.route('/api/section/<int:section_id>/exercises/<int:level>')
@login_required
def get_exercises(section_id, level):
    """جلب التمارين حسب المستوى"""
    exercises = Exercise.query.filter_by(
        section_id=section_id,
        level=level
    ).all()
    
    exercises_data = [exercise_to_dict(ex) for ex in exercises]
    
    return jsonify(exercises_data)

# ===================== تهيئة قاعدة البيانات =====================

def init_database():
    """تهيئة قاعدة البيانات وإنشاء بيانات تجريبية"""
    with app.app_context():
        # إنشاء الجداول
        db.create_all()
        print("✅ تم إنشاء جداول قاعدة البيانات")
        
        # التحقق من وجود المعلم الرئيسي
        if not User.query.filter_by(email='teacher@example.com').first():
            teacher = User(
                name='المعلم الإداري',
                email='teacher@example.com',
                user_type='teacher'
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            db.session.commit()
            print("✅ تم إنشاء المعلم الرئيسي")
        
        # التحقق من وجود درس تجريبي
        if not Lesson.query.first():
            teacher = User.query.filter_by(user_type='teacher').first()
            
            # إنشاء درس تجريبي
            lesson = Lesson(
                title='مقدمة في الرياضيات',
                description='تعلم أساسيات العمليات الحسابية',
                level_id=1,
                order=1,
                teacher_id=teacher.id,
                is_published=True
            )
            db.session.add(lesson)
            
            # إنشاء فقرة تجريبية
            section = Section(
                title='الجمع والطرح',
                content='<h3>مرحباً بك في درس الرياضيات</h3><p>سنتعلم معاً أساسيات الجمع والطرح.</p>',
                lesson_id=lesson.id,
                order=1
            )
            db.session.add(section)
            
            db.session.commit()
            print("✅ تم إنشاء بيانات تجريبية")
        
        print("🎉 قاعدة البيانات جاهزة للاستخدام")

# ===================== نقطة الدخول الرئيسية =====================

if __name__ == '__main__':
    print("\n🔄 جارٍ تهيئة قاعدة البيانات...")
    init_database()
    
    print("\n🌐 بدء تشغيل الخادم...")
    print("📍 العنوان: http://localhost:5000")
    print("📍 العنوان: http://127.0.0.1:5000")
    print("\n🎯 معلومات الدخول:")
    print("   المعلم: teacher@example.com / teacher123")
    print("   الطالب: سجل حساباً جديداً")
    print("\n" + "=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)