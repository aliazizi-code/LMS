
# 🎓 سامانه مدیریت یادگیری (LMS)

---

<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/1055/1055672.png" width="100" alt="LMS Logo"/>
</p>

---

## 📌 معرفی پروژه

این پروژه یک سامانه مدیریت یادگیری (Learning Management System) است که با استفاده از فریم‌ورک **Django** توسعه یافته است.  
سیستم به گونه‌ای طراحی شده که برای **ابعاد بزرگ و کاربران متعدد** کاملاً مناسب و مقیاس‌پذیر باشد.  

هدف این پروژه ایجاد بستری بهینه، تمیز و قابل توسعه برای مدیریت دوره‌های آموزشی، کاربران، نظرات و محتوای آموزشی است.

---

## 🧱 ساختار پروژه

پروژه به صورت ماژولار و سازمان‌یافته طراحی شده است.  
هر اپلیکیشن در فولدر جداگانه قرار دارد:

```
.
├── accounts/
├── comments/
├── core/
├── courses/
├── utils/
├── VisitCounter/
├── example.env.txt
├── manage.py
└── requirements.txt
```

---

## ⚙️ تکنولوژی‌ها و ابزارها



<p align="center">
  <a href="https://www.python.org/" target="_blank">
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://www.djangoproject.com/" target="_blank">
    <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  </a>
  <a href="https://www.django-rest-framework.org/" target="_blank">
    <img src="https://img.shields.io/badge/DRF-red?style=for-the-badge&logo=django&logoColor=white" alt="DRF">
  </a>
  <a href="https://docs.celeryq.dev/" target="_blank">
    <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery">
  </a>
  <a href="https://redis.io/" target="_blank">
    <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  </a>
  <a href="https://jwt.io/" target="_blank">
    <img src="https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT">
  </a>
  <a href="https://www.postgresql.org/" target="_blank">
    <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  </a>
  <a href="https://git-scm.com/" target="_blank">
    <img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" alt="Git">
  </a>
  <a href="https://www.postman.com/" target="_blank">
    <img src="https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white" alt="Postman">
  </a>
  <a href="https://ubuntu.com/" target="_blank">
    <img src="https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white" alt="Ubuntu">
  </a>
  <a href="https://code.visualstudio.com/" target="_blank">
    <img src="https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="VS Code">
  </a>
  <a href="https://github.com/features/copilot" target="_blank">
    <img src="https://img.shields.io/badge/Copilot-black?style=for-the-badge&logo=githubcopilot&logoColor=white" alt="Copilot">
  </a>
</p>

پکیج‌های جانبی مهم:  
- django-filter  
- drf-spectacular  
- django-taggit  
- pyotp  

---

## 🔍 توضیح مختصر اپلیکیشن‌ها

- **accounts**  
  مدیریت ورود، ثبت‌نام با OTP و رمز عبور، پروفایل‌های کاربری و کارمندی  

- **courses**  
  مدیریت دوره‌ها، فصل‌بندی یا جلسه‌ای، تگ‌ها، اساتید، پیش‌نیاز، زبان، بنر و ویدیوها  

- **comments**  
  سیستم کامنت‌دهی کنترل‌شده برای دوره‌ها و مقالات با تایید ادمین  

- **VisitCounter**  
  شمارش بازدیدهای یونیک و غیر یونیک با Redis و انتقال داده‌ها به PostgreSQL با Celery  

- **utils**  
  ابزارها و کلاس‌های کمکی، فیلدهای سفارشی، مدیریت OTP و کش  

---

## ⚙️ راه‌اندازی پروژه

برای اجرای پروژه به Python و یک محیط مجازی نیاز است.  
سایر پیش‌نیازها مانند دیتابیس، Redis و Celery باید توسط کاربر نصب و راه‌اندازی شوند.

### مراحل کلی:

```bash
git clone <repository-url>
python -m venv venv
source venv/bin/activate  # یا .\venv\Scripts\activate در ویندوز
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## 🧪 تست‌ها

- تست‌ها فقط برای اپلیکیشن **accounts** با unittest نوشته شده‌اند.  
- اجرای تست‌ها:  
```bash
python manage.py test accounts
```

---

## ⭐ نکات مهم پروژه

- بهینه بودن سیستم برای کاهش مصرف منابع و افزایش سرعت پاسخ‌دهی اهمیت بالایی داشت  
- طراحی سیستم به صورت قابل توسعه و مقیاس‌پذیر بود  
- تاکید بر کد تمیز (Clean Code) و معماری مناسب برای راحتی نگهداری و توسعه  
- دقت ویژه در طراحی دیتابیس برای پشتیبانی از عملکرد بهینه و ارتباطات درست داده‌ها

---

## 📚 جمع‌بندی پروژه

این سامانه مدیریت یادگیری (LMS) با تمرکز بر بهینه‌سازی، مقیاس‌پذیری و ساختار ماژولار طراحی شده است تا بتواند نیازهای آموزشی کاربران مختلف را پوشش دهد.  
این پروژه با بهره‌گیری از تکنولوژی‌های مدرن و استانداردهای کدنویسی، بستری قوی و قابل اعتماد برای مدیریت دوره‌ها، کاربران و محتوای آموزشی فراهم می‌کند.

---

_پایان مستندات پروژه LMS_
