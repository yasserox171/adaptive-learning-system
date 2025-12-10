"""
===============================================================================
app.py - نظام التعلم التكيفي الكامل
إصدار متوافق مع Flask 2.3.3 و SQLAlchemy 3.0.5
===============================================================================
نظام تعليمي تكيفي يتكيف مع مستوى كل طالب حسب أدائه في الاختبارات التشخيصية
الميزات:
1. نظام مستخدمين مزدوج (طلاب ومعلمين)
2. نظام تعليمي تكيفي بخمس مراحل
3. واجهة إدارة كاملة للمعلمين
4. قاعدة بيانات علائقية متكاملة
5. واجهة مستخدم عربية متجاوبة
===============================================================================
"""

# =============================================================================
# القسم 1: استيراد المكتبات والتهيئة
# =============================================================================

import sys
import os
import json
import re
from datetime import datetime
from functools import wraps

# طباعة معلومات النظام للمساعدة في استكشاف الأخطاء
print("=" * 70)
print("🚀 بدء تشغيل نظام التعلم التكيفي")
print("=" * 70)
print(f"🐍 إصدار Python: {sys.version}")
print(f"📁 المسار الحالي: {os.getcwd()}")
print(f"📊 نظام التشغيل: {os.name}")

try:
    # =========================================================================
    # 1.1 استيراد مكتبات Flask الأساسية
    # =========================================================================
    print("\n📦 جارٍ استيراد مكتبات Flask...")
    
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
    print("   ✅ Flask - إطار العمل الرئيسي")
    
    from flask_sqlalchemy import SQLAlchemy
    print("   ✅ Flask-SQLAlchemy - إدارة قواعد البيانات")
    
    from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
    print("   ✅ Flask-Login - إدارة جلسات المستخدمين")
    
    from werkzeug.security import generate_password_hash, check_password_hash
    print("   ✅ Werkzeug Security - تشفير كلمات المرور")
    
    from markupsafe import Markup
    print("   ✅ MarkupSafe - معالجة النصوص الآمنة")
    
    print("\n🎉 تم استيراد جميع المكتبات بنجاح!")
    
except ImportError as e:
    print(f"\n❌ خطأ في استيراد المكتبات: {e}")
    print("\n🔧 حل المشكلة:")
    print("1. تأكد من تفعيل البيئة الافتراضية:")
    print("   venv\\Scripts\\activate")
    print("\n2. قم بتثبيت المكتبات المطلوبة:")
    print("   pip install Flask==2.3.3 Werkzeug==2.3.7 Flask-Login==0.6.3 Flask-SQLAlchemy==3.0.5")
    sys.exit(1)


# =============================================================================
# القسم 2: تهيئة تطبيق Flask والإعدادات
# =============================================================================

print("\n⚙️  جارٍ تهيئة تطبيق Flask...")

# إنشاء تطبيق Flask مع مجلدات القوالب والملفات الثابتة
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# =========================================================================
# 2.1 إعدادات التطبيق الأساسية
# =========================================================================
app.config['SECRET_KEY'] = 'dev-secret-key-change-this-in-production'  # تغيير هذا في الإنتاج
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adaptive_learning.db'  # قاعدة بيانات SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # تحسين الأداء
app.config['TEMPLATES_AUTO_RELOAD'] = True  # إعادة تحميل القوالب تلقائياً

# =========================================================================
# 2.2 تهيئة الإضافات (Extensions)
# =========================================================================
db = SQLAlchemy(app)  # تهيئة قاعدة البيانات

# تهيئة نظام إدارة تسجيل الدخول
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # الصفحة التي يتم توجيه المستخدم إليها عند الحاجة للتسجيل
login_manager.login_message = '⚠️ يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'warning'


# =============================================================================
# القسم 3: نماذج قاعدة البيانات (Database Models)
# =============================================================================
print("🗄️  جارٍ تعريف نماذج قاعدة البيانات...")

class User(UserMixin, db.Model):
    """
    ========================================================================
    نموذج المستخدم (User Model)
    ------------------------------------------------------------------------
    يمثل مستخدمي النظام (طلاب أو معلمين)
    يحتوي على معلومات الحساب الأساسية وعلاقات مع النماذج الأخرى
    ========================================================================
    """
    __tablename__ = 'users'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment="الاسم الكامل للمستخدم")
    email = db.Column(db.String(100), unique=True, nullable=False, index=True, comment="البريد الإلكتروني (فريد)")
    password_hash = db.Column(db.String(200), nullable=False, comment="كلمة المرور مشفرة")
    user_type = db.Column(db.String(20), default='student', comment="نوع المستخدم: student أو teacher")
    level = db.Column(db.Integer, default=1, comment="المستوى التعليمي الحالي")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="تاريخ إنشاء الحساب")
    
    # العلاقات (Foreign Keys & Relationships)
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')
    created_lessons = db.relationship('Lesson', backref='teacher', lazy=True, cascade='all, delete-orphan')
    
    # طرق (Methods)
    def set_password(self, password):
        """تشفير كلمة المرور قبل حفظها"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من صحة كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def is_teacher(self):
        """التحقق إذا كان المستخدم معلم"""
        return self.user_type == 'teacher'
    
    def __repr__(self):
        """تمثيل نصي للكائن (لأغراض التصحيح)"""
        return f'<User {self.id}: {self.name} ({self.user_type})>'


class Lesson(db.Model):
    """
    ========================================================================
    نموذج الدرس (Lesson Model)
    ------------------------------------------------------------------------
    يمثل درساً تعليمياً يحتوي على فقرات متعددة
    يمكن إنشاؤه من قبل المعلمين وعرضه للطلاب
    ========================================================================
    """
    __tablename__ = 'lessons'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, comment="عنوان الدرس")
    description = db.Column(db.Text, comment="وصف مختصر للدرس")
    level_id = db.Column(db.Integer, default=1, comment="المستوى التعليمي للدرس (1-3)")
    order = db.Column(db.Integer, default=0, comment="ترتيب العرض بين الدروس")
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment="المعلم المنشئ")
    is_published = db.Column(db.Boolean, default=False, comment="هل الدرس منشور للطلاب؟")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="تاريخ الإنشاء")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="تاريخ آخر تعديل")
    
    # العلاقات
    sections = db.relationship('Section', backref='lesson', lazy=True, 
                               order_by='Section.order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lesson {self.id}: {self.title}>'


class Section(db.Model):
    """
    ========================================================================
    نموذج الفقرة (Section Model)
    ------------------------------------------------------------------------
    يمثل فقرة داخل درس، تحتوي على:
    1. اختبار تشخيصي
    2. تذكيرين (للمستويين المتقدم والأساسي)
    3. تمارين متنوعة
    ========================================================================
    """
    __tablename__ = 'sections'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, comment="عنوان الفقرة")
    content = db.Column(db.Text, nullable=False, comment="المحتوى التعليمي للفقرة")
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False, index=True)
    order = db.Column(db.Integer, default=0, comment="ترتيب الفقرة داخل الدرس")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="تاريخ الإنشاء")
    
    # العلاقات
    diagnostics = db.relationship('Diagnostic', backref='section', lazy=True, 
                                  cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='section', lazy=True, 
                                cascade='all, delete-orphan')
    exercises = db.relationship('Exercise', backref='section', lazy=True, 
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Section {self.id}: {self.title} (Lesson: {self.lesson_id})>'


class Diagnostic(db.Model):
    """
    ========================================================================
    نموذج الاختبار التشخيصي (Diagnostic Model)
    ------------------------------------------------------------------------
    اختبار قصير في بداية كل فقرة لتحديد مستوى الطالب
    النتيجة تحدد المسار التعليمي (مستوى 1 أو 2)
    ========================================================================
    """
    __tablename__ = 'diagnostics'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.Text, nullable=False, comment="سؤال الاختبار")
    options = db.Column(db.Text, comment="خيارات الإجابة بتنسيق JSON")
    correct_answer = db.Column(db.String(10), nullable=False, comment="الإجابة الصحيحة")
    explanation = db.Column(db.Text, comment="شرح الإجابة")
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False, index=True)
    
    def get_options_list(self):
        """تحويل خيارات JSON إلى قائمة Python"""
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def __repr__(self):
        return f'<Diagnostic {self.id} (Section: {self.section_id})>'


class Reminder(db.Model):
    """
    ========================================================================
    نموذج التذكير (Reminder Model)
    ------------------------------------------------------------------------
    مراجعات تعليمية مخصصة حسب مستوى الطالب:
    - Type 1: للمستوى المتقدم (N ≥ 10)
    - Type 2: للمستوى الأساسي (N < 10)
    ========================================================================
    """
    __tablename__ = 'reminders'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_type = db.Column(db.Integer, nullable=False, comment="نوع التذكير: 1 (متقدم) أو 2 (أساسي)")
    title = db.Column(db.String(200), comment="عنوان التذكير")
    content = db.Column(db.Text, nullable=False, comment="محتوى التذكير التعليمي")
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False, index=True)
    
    # العلاقات
    exercises = db.relationship('Exercise', backref='reminder', lazy=True, 
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        type_name = "متقدم" if self.reminder_type == 1 else "أساسي"
        return f'<Reminder {self.id}: {self.title} ({type_name})>'


class Exercise(db.Model):
    """
    ========================================================================
    نموذج التمرين (Exercise Model)
    ------------------------------------------------------------------------
    تمارين تعليمية متنوعة حسب المستوى:
    - Level 0: تمرين أساسي (للجميع)
    - Level 1: تمارين متقدمة (للمستوى 1)
    - Level 2: تمارين علاجية (للمستوى 2)
    ========================================================================
    """
    __tablename__ = 'exercises'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), comment="عنوان التمرين")
    content = db.Column(db.Text, nullable=False, comment="نص التمرين")
    level = db.Column(db.Integer, default=0, comment="مستوى التمرين: 0, 1, أو 2")
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), index=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), index=True)
    correct_answer = db.Column(db.String(500), nullable=False, comment="الإجابة الصحيحة")
    explanation = db.Column(db.Text, comment="شرح طريقة الحل")
    points = db.Column(db.Integer, default=10, comment="عدد النقاط للإجابة الصحيحة")
    
    def __repr__(self):
        level_names = {0: "أساسي", 1: "متقدم", 2: "علاجي"}
        return f'<Exercise {self.id}: {self.title} ({level_names.get(self.level, "غير معروف")})>'


class Result(db.Model):
    """
    ========================================================================
    نموذج النتيجة (Result Model)
    ------------------------------------------------------------------------
    يسجل نتائج الطلاب في الاختبارات والتمارين
    يستخدم لمتابعة التقدم وتحليل الأداء
    ========================================================================
    """
    __tablename__ = 'results'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False, index=True)
    diagnostic_id = db.Column(db.Integer, db.ForeignKey('diagnostics.id'), index=True)
    is_correct = db.Column(db.Boolean, nullable=False, comment="هل الإجابة صحيحة؟")
    answer = db.Column(db.Text, comment="إجابة الطالب")
    score = db.Column(db.Integer, default=0, comment="الدرجة المحصلة")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment="وقت التسجيل")
    
    def __repr__(self):
        return f'<Result Student:{self.student_id} Exercise:{self.exercise_id} Score:{self.score}>'


# =============================================================================
# القسم 4: فلاتر Jinja2 المخصصة (Custom Template Filters)
# =============================================================================
print("🎨 جارٍ تعريف فلاتر Jinja2 المخصصة...")

@app.template_filter('from_json')
def from_json_filter(value):
    """
    ========================================================================
    فلتر from_json
    ------------------------------------------------------------------------
    يحول سلسلة JSON إلى كائن Python
    يستخدم لعرض خيارات الاختبارات التشخيصية
    ========================================================================
    """
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

@app.template_filter('striptags')
def striptags_filter(value):
    """
    ========================================================================
    فلتر striptags
    ------------------------------------------------------------------------
    يزيل الوسوم HTML من النص لعرضه كمحتوى نصي خالص
    ========================================================================
    """
    if not value:
        return ''
    return re.sub(r'<[^>]*>', '', str(value))

@app.template_filter('safe')
def safe_filter(value):
    """
    ========================================================================
    فلتر safe
    ------------------------------------------------------------------------
    يسمح بعرض HTML دون escaping
    يستخدم لعرض المحتوى التعليمي الذي يحتوي على تنسيق HTML
    ========================================================================
    """
    return Markup(value)


# =============================================================================
# القسم 5: دوال تحويل النماذج (Model Conversion Functions)
# =============================================================================

def exercise_to_dict(exercise):
    """
    ========================================================================
    تحويل كائن Exercise إلى Dictionary
    ------------------------------------------------------------------------
    يجعل الكائن قابلاً للتسلسل إلى JSON
    يستخدم في واجهات API وتحميل البيانات في JavaScript
    ========================================================================
    """
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
    """
    ========================================================================
    تحويل كائن Reminder إلى Dictionary
    ========================================================================
    """
    return {
        'id': reminder.id,
        'title': reminder.title or f'تذكير المستوى {reminder.reminder_type}',
        'content': reminder.content,
        'reminder_type': reminder.reminder_type,
        'exercises': [exercise_to_dict(ex) for ex in reminder.exercises]
    }

def diagnostic_to_dict(diagnostic):
    """
    ========================================================================
    تحويل كائن Diagnostic إلى Dictionary
    ========================================================================
    """
    return {
        'id': diagnostic.id,
        'question': diagnostic.question,
        'options': diagnostic.get_options_list(),
        'correct_answer': diagnostic.correct_answer,
        'explanation': diagnostic.explanation or ''
    }


# =============================================================================
# القسم 6: دوال المساعدة (Helper Functions)
# =============================================================================
print("🔧 جارٍ تعريف دوال المساعدة...")

@login_manager.user_loader
def load_user(user_id):
    """
    ========================================================================
    تحميل المستخدم من قاعدة البيانات
    ------------------------------------------------------------------------
    دالة مطلوبة من قبل Flask-Login
    تحمل كائن المستخدم من ID المخزن في جلسة المستخدم
    ========================================================================
    """
    return User.query.get(int(user_id))

def teacher_required(f):
    """
    ========================================================================
    ديكوراتور teacher_required
    ------------------------------------------------------------------------
    يضمن أن المستخدم المسجل دخولاً هو معلم
    يحمي مسارات المعلمين من الوصول غير المصرح به
    ========================================================================
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # التحقق من تسجيل الدخول
        if not current_user.is_authenticated:
            flash('⚠️ يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        
        # التحقق من أن المستخدم معلم
        if not current_user.is_teacher():
            flash('🚫 هذه الصفحة للمعلمين فقط', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function


# =============================================================================
# القسم 7: مسارات الصفحات العامة (Public Routes)
# =============================================================================
print("🌐 جارٍ تعريف مسارات الصفحات...")

@app.route('/')
def index():
    """
    ========================================================================
    الصفحة الرئيسية (Home Page)
    ------------------------------------------------------------------------
    نقطة الدخول الرئيسية للتطبيق
    إذا كان المستخدم مسجل دخولاً، يتم توجيهه إلى لوحة التحكم
    وإلا، يتم عرض صفحة الترحيب
    ========================================================================
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    ========================================================================
    صفحة تسجيل الدخول (Login Page)
    ------------------------------------------------------------------------
    معالجة تسجيل دخول المستخدمين (طلاب ومعلمين)
    التحقق من صحة بيانات الاعتماد وإنشاء جلسة المستخدم
    ========================================================================
    """
    # إذا كان المستخدم مسجلاً دخولاً بالفعل
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # استخراج البيانات من النموذج
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # البحث عن المستخدم في قاعدة البيانات
        user = User.query.filter_by(email=email).first()
        
        # التحقق من صحة بيانات الاعتماد
        if user and user.check_password(password):
            login_user(user)  # إنشاء جلسة المستخدم
            flash(f'✅ مرحباً بعودتك، {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    ========================================================================
    صفحة التسجيل (Registration Page)
    ------------------------------------------------------------------------
    إنشاء حسابات جديدة للطلاب والمعلمين
    التحقق من عدم تكرار البريد الإلكتروني
    ========================================================================
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # استخراج البيانات من النموذج
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'student')
        
        # التحقق من صحة المدخلات
        if not name or not email or not password:
            flash('⚠️ جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('register'))
        
        # التحقق من عدم وجود المستخدم مسبقاً
        if User.query.filter_by(email=email).first():
            flash('❌ البريد الإلكتروني مسجل مسبقاً', 'danger')
            return redirect(url_for('register'))
        
        # إنشاء المستخدم الجديد
        user = User(name=name, email=email, user_type=user_type)
        user.set_password(password)  # تشفير كلمة المرور
        
        # حفظ المستخدم في قاعدة البيانات
        db.session.add(user)
        db.session.commit()
        
        # تسجيل دخول المستخدم الجديد
        login_user(user)
        flash(f'🎉 تم إنشاء حسابك بنجاح كـ {user_type}', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """
    ========================================================================
    تسجيل الخروج (Logout)
    ------------------------------------------------------------------------
    إنهاء جلسة المستخدم الحالية
    ========================================================================
    """
    logout_user()
    flash('👋 تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """
    ========================================================================
    لوحة التحكم (Dashboard)
    ------------------------------------------------------------------------
    الصفحة الرئيسية بعد تسجيل الدخول
    تعرض واجهات مختلفة للطلاب والمعلمين
    ========================================================================
    """
    if current_user.is_teacher():
        # لوحة تحكم المعلم
        lessons = Lesson.query.filter_by(teacher_id=current_user.id).order_by(Lesson.order).all()
        return render_template('teacher_dashboard.html', 
                             lessons=lessons, 
                             teacher=current_user)
    else:
        # لوحة تحكم الطالب
        lessons = Lesson.query.filter_by(is_published=True).order_by(Lesson.order).all()
        return render_template('student_dashboard.html', 
                             lessons=lessons, 
                             student=current_user)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    """
    ========================================================================
    عرض الدرس (View Lesson)
    ------------------------------------------------------------------------
    عرض صفحة الدرس مع قائمة فقراته
    ========================================================================
    """
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # التحقق من صلاحيات الوصول
    if not lesson.is_published and not current_user.is_teacher():
        flash('⏳ هذا الدرس غير متاح حالياً', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('lesson.html', lesson=lesson)

@app.route('/section/<int:section_id>')
@login_required
def view_section(section_id):
    """
    ========================================================================
    عرض الفقرة (View Section)
    ------------------------------------------------------------------------
    عرض صفحة الفقرة مع دورة التعلم التكيفية الكاملة:
    1. التشخيص → 2. التذكيرات → 3. المحتوى → 4. التمارين
    ========================================================================
    """
    section = Section.query.get_or_404(section_id)
    
    # التحقق من صلاحيات الوصول
    if not section.lesson.is_published and not current_user.is_teacher():
        flash('⏳ هذا الدرس غير متاح حالياً', 'warning')
        return redirect(url_for('dashboard'))
    
    # تحويل البيانات إلى تنسيق قابل للتسلسل
    diagnostics_data = [diagnostic_to_dict(d) for d in section.diagnostics]
    
    # تجميع التمارين حسب المستوى
    main_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 0]
    advanced_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 1]
    basic_exercises = [exercise_to_dict(ex) for ex in section.exercises if ex.level == 2]
    
    # التحقق من وجود نتائج تشخيص سابقة للطالب
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
# القسم 8: مسارات المعلمين (Teacher Routes)
# =============================================================================

@app.route('/teacher/lessons')
@login_required
@teacher_required
def teacher_lessons():
    """
    ========================================================================
    صفحة إدارة الدروس (Manage Lessons)
    ------------------------------------------------------------------------
    عرض جميع الدروس التي أنشأها المعلم
    ========================================================================
    """
    lessons = Lesson.query.filter_by(teacher_id=current_user.id)\
               .order_by(Lesson.order.desc()).all()
    return render_template('teacher/lessons.html', lessons=lessons)

@app.route('/teacher/lesson/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_lesson():
    """
    ========================================================================
    إنشاء درس جديد (Create New Lesson)
    ------------------------------------------------------------------------
    استمارة لإضافة درس جديد
    ========================================================================
    """
    if request.method == 'POST':
        # استخراج البيانات من النموذج
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level_id = request.form.get('level_id', 1, type=int)
        
        # التحقق من صحة المدخلات
        if not title:
            flash('⚠️ عنوان الدرس مطلوب', 'warning')
            return redirect(url_for('create_lesson'))
        
        # حساب الترتيب التلقائي
        next_order = Lesson.query.filter_by(teacher_id=current_user.id).count() + 1
        
        # إنشاء الدرس الجديد
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
    """
    ========================================================================
    تعديل درس (Edit Lesson)
    ------------------------------------------------------------------------
    استمارة لتعديل معلومات الدرس وإضافة الفقرات
    ========================================================================
    """
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # التحقق من ملكية الدرس
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لتعديل هذا الدرس', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        # تحديث بيانات الدرس
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
    """
    ========================================================================
    حذف درس (Delete Lesson)
    ------------------------------------------------------------------------
    حذف درس مع جميع فقراته وتمارينه
    ========================================================================
    """
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
    """
    ========================================================================
    إنشاء فقرة جديدة (Create New Section)
    ------------------------------------------------------------------------
    استمارة لإضافة فقرة جديدة داخل درس
    ========================================================================
    """
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
        
        # حساب الترتيب التلقائي
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
    ------------------------------------------------------------------------
    استمارة لتعديل محتوى الفقرة
    ========================================================================
    """
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لتعديل هذه الفقرة', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        section.title = request.form.get('title', '').strip()
        section.content = request.form.get('content', '').strip()
        section.order = request.form.get('order', 0, type=int)
        
        db.session.commit()
        flash('✅ تم تحديث الفقرة بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section.id))
    
    return render_template('teacher/edit_section.html', 
                         section=section, 
                         lesson=lesson)

@app.route('/teacher/section/<int:section_id>/diagnostic/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_diagnostic(section_id):
    """
    ========================================================================
    إنشاء اختبار تشخيصي (Create Diagnostic)
    ------------------------------------------------------------------------
    استمارة لإضافة اختبار تشخيصي للفقرة
    ========================================================================
    """
    section = Section.query.get_or_404(section_id)
    lesson = section.lesson
    
    if lesson.teacher_id != current_user.id:
        flash('🚫 ليس لديك صلاحية لإضافة اختبار تشخيصي', 'danger')
        return redirect(url_for('teacher_lessons'))
    
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        option1 = request.form.get('option1', '').strip()
        option2 = request.form.get('option2', '').strip()
        option3 = request.form.get('option3', '').strip()
        option4 = request.form.get('option4', '').strip()
        correct_answer = request.form.get('correct_answer', '').strip()
        explanation = request.form.get('explanation', '').strip()
        
        # التحقق من صحة المدخلات
        if not question or not correct_answer:
            flash('⚠️ السؤال والإجابة الصحيحة مطلوبان', 'warning')
            return redirect(url_for('create_diagnostic', section_id=section_id))
        
        # تحويل الخيارات إلى JSON
        options = json.dumps([option1, option2, option3, option4])
        
        diagnostic = Diagnostic(
            question=question,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            section_id=section_id
        )
        
        db.session.add(diagnostic)
        db.session.commit()
        
        flash('✅ تم إنشاء الاختبار التشخيصي بنجاح', 'success')
        return redirect(url_for('edit_section', section_id=section_id))
    
    return render_template('teacher/create_diagnostic.html', section=section)

@app.route('/teacher/section/<int:section_id>/reminder/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_reminder(section_id):
    """
    ========================================================================
    إنشاء تذكير (Create Reminder)
    ------------------------------------------------------------------------
    استمارة لإضافة تذكير (متقدم أو أساسي) للفقرة
    ========================================================================
    """
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
    """
    ========================================================================
    إنشاء تمرين (Create Exercise)
    ------------------------------------------------------------------------
    استمارة لإضافة تمرين (أساسي، متقدم، أو علاجي)
    ========================================================================
    """
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
    """
    ========================================================================
    صفحة الإحصائيات (Statistics Page)
    ------------------------------------------------------------------------
    عرض إحصائيات عامة عن النظام وأداء الطلاب
    ========================================================================
    """
    # إحصائيات المعلم
    total_lessons = Lesson.query.filter_by(teacher_id=current_user.id).count()
    published_lessons = Lesson.query.filter_by(teacher_id=current_user.id, 
                                              is_published=True).count()
    total_students = User.query.filter_by(user_type='student').count()
    
    return render_template('teacher/statistics.html',
                         total_lessons=total_lessons,
                         published_lessons=published_lessons,
                         total_students=total_students)

# مسارات حذف العناصر (Delete Routes)
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


# =============================================================================
# القسم 9: واجهات API (API Routes)
# =============================================================================

@app.route('/api/diagnostic/<int:diagnostic_id>', methods=['POST'])
@login_required
def submit_diagnostic(diagnostic_id):
    """
    ========================================================================
    تقديم إجابة الاختبار التشخيصي (Submit Diagnostic)
    ------------------------------------------------------------------------
    API لتسجيل إجابة الطالب على الاختبار التشخيصي
    تحدد مستوى الطالب (1 أو 2) بناءً على النتيجة
    ========================================================================
    """
    diagnostic = Diagnostic.query.get_or_404(diagnostic_id)
    data = request.get_json()
    
    if not data or 'answer' not in data:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'}), 400
    
    # التحقق من صحة الإجابة
    is_correct = data['answer'] == diagnostic.correct_answer
    score = 10 if is_correct else 0
    level = 1 if score >= 10 else 2  # تحديد المستوى
    
    # حفظ النتيجة
    result = Result(
        student_id=current_user.id,
        diagnostic_id=diagnostic_id,
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
        'level': level,
        'explanation': diagnostic.explanation or ''
    })

@app.route('/api/exercise/<int:exercise_id>', methods=['POST'])
@login_required
def submit_exercise(exercise_id):
    """
    ========================================================================
    تقديم إجابة التمرين (Submit Exercise)
    ------------------------------------------------------------------------
    API لتسجيل إجابة الطالب على التمرين
    ========================================================================
    """
    exercise = Exercise.query.get_or_404(exercise_id)
    data = request.get_json()
    
    if not data or 'answer' not in data:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'}), 400
    
    # التحقق من صحة الإجابة
    is_correct = data['answer'] == exercise.correct_answer
    score = exercise.points if is_correct else 0
    
    # حفظ النتيجة
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
    """
    ========================================================================
    جلب التذكيرات (Get Reminders)
    ------------------------------------------------------------------------
    API لجلب التذكيرات حسب مستوى الطالب
    ========================================================================
    """
    reminders = Reminder.query.filter_by(
        section_id=section_id,
        reminder_type=level
    ).all()
    
    reminders_data = [reminder_to_dict(reminder) for reminder in reminders]
    
    return jsonify(reminders_data)

@app.route('/api/section/<int:section_id>/exercises/<int:level>')
@login_required
def get_exercises(section_id, level):
    """
    ========================================================================
    جلب التمارين (Get Exercises)
    ------------------------------------------------------------------------
    API لجلب التمارين حسب مستوى الطالب
    ========================================================================
    """
    exercises = Exercise.query.filter_by(
        section_id=section_id,
        level=level
    ).all()
    
    exercises_data = [exercise_to_dict(exercise) for exercise in exercises]
    
    return jsonify(exercises_data)


# =============================================================================
# القسم 10: تهيئة قاعدة البيانات (Database Initialization)
# =============================================================================

def init_database():
    """
    ========================================================================
    تهيئة قاعدة البيانات (Initialize Database)
    ------------------------------------------------------------------------
    إنشاء الجداول وإضافة بيانات تجريبية للمرة الأولى
    ========================================================================
    """
    print("\n" + "=" * 60)
    print("🗃️  جارٍ تهيئة قاعدة البيانات...")
    print("=" * 60)
    
    with app.app_context():
        # 1. إنشاء جميع الجداول
        db.create_all()
        print("✅ تم إنشاء جداول قاعدة البيانات")
        
        # 2. التحقق من وجود المعلم الرئيسي
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
        else:
            print("📌 المعلم الرئيسي موجود مسبقاً")
        
        # 3. التحقق من وجود درس تجريبي
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
            
            # إنشاء اختبار تشخيصي تجريبي
            diagnostic = Diagnostic(
                question='ما هو ناتج 5 + 3؟',
                options=json.dumps(['6', '7', '8', '9']),
                correct_answer='8',
                explanation='5 + 3 = 8',
                section_id=section.id
            )
            db.session.add(diagnostic)
            
            # إنشاء تذكير للمستوى المتقدم
            reminder1 = Reminder(
                reminder_type=1,
                title='مراجعة سريعة للجمع',
                content='الجمع هو عملية تجميع كميتين أو أكثر للحصول على كمية أكبر.',
                section_id=section.id
            )
            db.session.add(reminder1)
            
            # إنشاء تذكير للمستوى الأساسي
            reminder2 = Reminder(
                reminder_type=2,
                title='شرح مفصل للجمع',
                content='لتعلم الجمع: ابدأ بالعدد الأول، ثم أضف العدد الثاني عداً.',
                section_id=section.id
            )
            db.session.add(reminder2)
            
            # إنشاء تمارين متنوعة
            exercises = [
                Exercise(
                    title='تمرين أساسي',
                    content='ما هو ناتج 4 + 2؟',
                    level=0,
                    section_id=section.id,
                    correct_answer='6',
                    explanation='4 + 2 = 6'
                ),
                Exercise(
                    title='تمرين متقدم',
                    content='ما هو ناتج 12 + 15؟',
                    level=1,
                    section_id=section.id,
                    correct_answer='27',
                    explanation='12 + 15 = 27'
                ),
                Exercise(
                    title='تمرين علاجي',
                    content='ما هو ناتج 1 + 1؟',
                    level=2,
                    section_id=section.id,
                    correct_answer='2',
                    explanation='1 + 1 = 2'
                )
            ]
            
            for exercise in exercises:
                db.session.add(exercise)
            
            db.session.commit()
            print("✅ تم إنشاء بيانات تعليمية تجريبية")
        else:
            print("📌 البيانات التجريبية موجودة مسبقاً")
        
        # 4. عرض ملخص قاعدة البيانات
        print("\n📊 ملخص قاعدة البيانات:")
        print(f"   👨‍🏫 المعلمون: {User.query.filter_by(user_type='teacher').count()}")
        print(f"   👨‍🎓 الطلاب: {User.query.filter_by(user_type='student').count()}")
        print(f"   📚 الدروس: {Lesson.query.count()}")
        print(f"   📝 الفقرات: {Section.query.count()}")
        
        print("\n🎉 قاعدة البيانات جاهزة للاستخدام!")


# =============================================================================
# القسم 11: نقطة الدخول الرئيسية (Main Entry Point)
# =============================================================================

if __name__ == '__main__':
    """
    ========================================================================
    نقطة الدخول الرئيسية للتطبيق
    ------------------------------------------------------------------------
    تهيئة قاعدة البيانات وتشغيل خادم التطوير
    ========================================================================
    """
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
    print("   3. للوصول من أجهزة أخرى: python app.py --host=0.0.0.0")
    
    print("\n" + "=" * 70)
    
    # تشغيل التطبيق
    try:
        app.run(
            debug=True,           # وضع التصحيح (غير مناسب للإنتاج)
            host='0.0.0.0',      # الاستماع على جميع الواجهات
            port=5000,           # المنفذ الافتراضي
            threaded=True        # معالجة متعددة الخيوط
        )
    except KeyboardInterrupt:
        print("\n\n👋 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {e}")
        print("🔧 حاول تشغيل: python -m flask run")
    
# =============================================================================
# نهاية ملف app.py
# =============================================================================