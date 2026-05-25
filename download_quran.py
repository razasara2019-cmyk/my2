#!/usr/bin/env python3
"""
download_quran.py – تحميل القرآن الكريم كاملاً من AlQuran Cloud API
يُشغل هذا الملف مرة واحدة فقط لتحميل القرآن وحفظه في ملف quran.json

الاستخدام: python download_quran.py
"""

import requests
import json
import os
import sys

def download_quran():
    """تحميل القرآن الكريم من API وحفظه كملف JSON"""
    
    print("=" * 60)
    print("🕋 تحميل القرآن الكريم")
    print("=" * 60)
    
    url = "https://api.alquran.cloud/v1/quran/ar.alafasy"
    
    try:
        print("📡 جاري الاتصال بـ AlQuran Cloud API...")
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ فشل التحميل: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("code") != 200:
            print(f"❌ فشل التحميل: {data.get('message', 'خطأ غير معروف')}")
            return False
        
        print("✅ تم استلام البيانات")
        
        # تحويل البيانات إلى صيغة منظمة
        quran_data = {
            "meta": {
                "name": "القرآن الكريم",
                "source": "https://api.alquran.cloud",
                "version": data.get("data", {}).get("version", "1.0"),
                "surahs_count": 114,
                "total_verses": 6236,
                "edition": "ar.alafasy"
            },
            "surahs": []
        }
        
        total_verses = 0
        
        for surah in data["data"]["surahs"]:
            surah_info = {
                "id": surah["number"],
                "name": surah["name"],
                "name_english": surah["englishName"],
                "name_arabic": surah["name"],
                "revelation_type": surah["revelationType"],
                "verses_count": len(surah["ayahs"]),
                "verses": []
            }
            
            for ayah in surah["ayahs"]:
                surah_info["verses"].append({
                    "id": ayah["numberInSurah"],
                    "number": ayah["number"],
                    "text": ayah["text"],
                    "juz": ayah.get("juz", 0),
                    "hizb": ayah.get("hizb", 0),
                    "page": ayah.get("page", 0)
                })
                total_verses += 1
            
            quran_data["surahs"].append(surah_info)
        
        # حفظ الملف
        with open("quran.json", "w", encoding="utf-8") as f:
            json.dump(quran_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ تم تحميل القرآن الكريم بنجاح!")
        print(f"   • عدد السور: {len(quran_data['surahs'])}")
        print(f"   • عدد الآيات: {total_verses}")
        print(f"   • حجم الملف: {os.path.getsize('quran.json') / 1024 / 1024:.2f} MB")
        print(f"\n📁 الموقع: {os.path.abspath('quran.json')}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ فشل التحميل: انتهى وقت الانتظار")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ فشل التحميل: لا يمكن الاتصال بالخادم")
        return False
    except Exception as e:
        print(f"❌ فشل التحميل: {e}")
        return False

if __name__ == "__main__":
    success = download_quran()
    sys.exit(0 if success else 1)
