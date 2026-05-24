#!/bin/bash
# ============================================================
# diagnose.sh – أداة تشخيص شاملة لخادم الكيان الدستوري الحي
# الإصدار: 1.0
# التاريخ: 2026-05-24
# ============================================================
# ينفذ هذا الملف فحوصات متعددة لتحديد سبب عدم استجابة الكيان
# يمكن تشغيله بأمان على الخادم، ولا يحتوي على أي مفاتيح سرية
# ============================================================

# الألوان لجعل الناتج مقروءاً
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# دالة لطباعة العناوين
print_section() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# دالة لطباعة النجاح
print_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

# دالة لطباعة التحذير
print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# دالة لطباعة الخطأ
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================
# بدء التشخيص
# ============================================================

print_section "🛡️ تشخيص الكيان الدستوري الحي - الإصدار 5.0a"
echo "الوقت: $(date)"
echo "الخادم: $(hostname)"

# ============================================================
# 1. التحقق من الخدمة (systemd)
# ============================================================

print_section "1. التحقق من خدمة systemd"

if systemctl list-units --full -all | grep -q "constitutional-mind.service"; then
    SERVICE_NAME="constitutional-mind.service"
elif systemctl list-units --full -all | grep -q "my2.service"; then
    SERVICE_NAME="my2.service"
else
    SERVICE_NAME="غير موجودة"
fi

if [ "$SERVICE_NAME" != "غير موجودة" ]; then
    STATUS=$(systemctl is-active $SERVICE_NAME)
    if [ "$STATUS" = "active" ]; then
        print_ok "الخدمة $SERVICE_NAME نشطة"
    else
        print_error "الخدمة $SERVICE_NAME غير نشطة (الحالة: $STATUS)"
    fi
    echo "تفاصيل الخدمة:"
    sudo systemctl status $SERVICE_NAME --no-pager -l 2>&1 | head -15
else
    print_warning "لم يتم العثور على خدمة systemd (قد يعمل الكيان يدوياً)"
fi

# ============================================================
# 2. السجلات (Logs)
# ============================================================

print_section "2. آخر 30 سطراً من السجلات"

if [ "$SERVICE_NAME" != "غير موجودة" ]; then
    LOGS=$(sudo journalctl -u $SERVICE_NAME -n 30 --no-pager 2>&1)
    if [ -n "$LOGS" ]; then
        echo "$LOGS"
    else
        print_warning "لا توجد سجلات للخدمة"
    fi
else
    print_warning "لا توجد خدمة systemd لعرض سجلاتها"
fi

# ============================================================
# 3. التحقق من العمليات العاملة
# ============================================================

print_section "3. التحقق من عمليات Python"

MAIN_PID=$(ps aux | grep "python3.*main.py" | grep -v grep | awk '{print $2}')
if [ -n "$MAIN_PID" ]; then
    print_ok "العملية main.py موجودة (PID: $MAIN_PID)"
    ps aux | grep -E "python3.*main.py" | grep -v grep
else
    print_error "لا توجد عملية main.py قيد التشغيل"
fi

# ============================================================
# 4. اختبار نقطة /health
# ============================================================

print_section "4. اختبار نقطة /health"

HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    print_ok "نقطة /health تستجيب (HTTP $HEALTH_RESPONSE)"
    curl -s http://localhost:8000/health 2>/dev/null | head -5
elif [ -n "$HEALTH_RESPONSE" ]; then
    print_error "نقطة /health تستجيب برمز خطأ: HTTP $HEALTH_RESPONSE"
else
    print_error "نقطة /health لا تستجيب (الخادم لا يعمل أو المنفذ مغلق)"
fi

# ============================================================
# 5. اختبار Groq API مباشرة
# ============================================================

print_section "5. اختبار Groq API مباشرة"

if [ -f ".env" ]; then
    GROQ_KEY=$(grep GROQ_API_KEY .env | cut -d '=' -f2 | tr -d ' ' | head -1)
    if [ -n "$GROQ_KEY" ] && [ "$GROQ_KEY" != "gsk_your_actual_key_here" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            https://api.groq.com/openai/v1/models \
            -H "Authorization: Bearer $GROQ_KEY" 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ]; then
            print_ok "Groq API يستجيب بشكل صحيح (HTTP $HTTP_CODE)"
        else
            print_error "Groq API لا يستجيب بشكل صحيح (HTTP $HTTP_CODE)"
            print_warning "قد يكون المفتاح غير صالح أو منتهياً"
        fi
    else
        print_error "مفتاح Groq API غير موجود أو غير صحيح في ملف .env"
    fi
else
    print_error "ملف .env غير موجود"
fi

# ============================================================
# 6. محتوى ملف .env (بدون المفتاح الكامل)
# ============================================================

print_section "6. محتوى ملف .env (تم إخفاء المفتاح)"

if [ -f ".env" ]; then
    cat .env | sed 's/gsk_[a-zA-Z0-9]*/gsk_REDACTED/g' | sed 's/ghp_[a-zA-Z0-9]*/ghp_REDACTED/g'
else
    print_error "ملف .env غير موجود"
fi

# ============================================================
# 7. اختبار نقطة /chat
# ============================================================

print_section "7. اختبار نقطة /chat"

CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "ping"}' 2>/dev/null)

if [ -n "$CHAT_RESPONSE" ]; then
    if echo "$CHAT_RESPONSE" | grep -q "error\|خطأ"; then
        print_error "نقطة /chat ردت بخطأ:"
        echo "$CHAT_RESPONSE" | head -10
    else
        print_ok "نقطة /chat تستجيب بشكل طبيعي"
        echo "$CHAT_RESPONSE" | head -10
    fi
else
    print_error "نقطة /chat لا تستجيب"
fi

# ============================================================
# 8. إصدار Python والمكتبات الرئيسية
# ============================================================

print_section "8. إصدار Python والمكتبات الرئيسية"

echo "Python: $(python3 --version 2>&1)"
echo ""

for PKG in embeddb fastapi groq uvicorn; do
    VERSION=$(pip show $PKG 2>/dev/null | grep Version | cut -d ' ' -f2)
    if [ -n "$VERSION" ]; then
        print_ok "$PKG: $VERSION"
    else
        print_error "$PKG: غير مثبت"
    fi
done

# ============================================================
# 9. استخدام الذاكرة
# ============================================================

print_section "9. استخدام الذاكرة"

free -h

# ============================================================
# 10. المنفذ 8000
# ============================================================

print_section "10. المنفذ 8000"

PORT_PID=$(sudo lsof -i :8000 -t 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    print_ok "المنفذ 8000 مشغول (PID: $PORT_PID)"
    sudo lsof -i :8000 2>/dev/null
else
    print_warning "المنفذ 8000 غير مشغول (الخادم لا يستمع)"
fi

# ============================================================
# انتهى التشخيص
# ============================================================

print_section "🏁 انتهى التشخيص"

echo "إذا كنت لا ترى أي أخطاء واضحة، أرسل هذا الناتج إلى الخبير."
echo "سيتمكن من تحديد المشكلة بدقة بناءً على هذه المعلومات."
