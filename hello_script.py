import datetime

def greet(name):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"مرحباً {name}!")
    print(f"الوقت الحالي: {now}")
    print("تم تشغيل السكريبت بنجاح على GitHub Actions ✅")

def calculate(a, b):
    print(f"\nعمليات حسابية بسيطة على {a} و {b}:")
    print(f"  الجمع:    {a} + {b} = {a + b}")
    print(f"  الطرح:    {a} - {b} = {a - b}")
    print(f"  الضرب:    {a} × {b} = {a * b}")
    print(f"  القسمة:   {a} ÷ {b} = {a / b:.2f}")

if __name__ == "__main__":
    greet("Claude")
    calculate(20, 4)
