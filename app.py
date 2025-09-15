from flask import Flask, request, render_template, redirect, url_for
from googletrans import Translator
import pyodbc
import re

app = Flask(__name__)
translator = Translator()

# Kết nối SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=HUY-PC\\MSSQLSERVER01;"
    "DATABASE=dichchuyennganh;"
    "Trusted_Connection=yes;"
)

def get_terms(module_id=None):
    cursor = conn.cursor()
    if module_id:
        cursor.execute("SELECT id, english, vietnamese, note FROM Terms WHERE module = ? ORDER BY english ASC", module_id)
    else:
        cursor.execute("SELECT id, english, vietnamese, note, module FROM Terms ORDER BY english ASC")
    return cursor.fetchall()

def preprocess_terms(text, module_id=None):
    placeholders = {}
    lower_text = text.lower()
    cursor = conn.cursor()
    if module_id:
        cursor.execute("SELECT english, vietnamese FROM Terms WHERE module = ?", module_id)
    else:
        cursor.execute("SELECT english, vietnamese FROM Terms")

    terms = cursor.fetchall()

    for i, (english, vietnamese) in enumerate(terms):
        eng_lower = english.lower()
        if eng_lower in lower_text:
            placeholder = f"[[TERM{i}]]"
            lower_text = lower_text.replace(eng_lower, placeholder)
            placeholders[placeholder] = f"{english} ({vietnamese})"
    return lower_text, placeholders


def postprocess_terms(text, placeholders):
    for placeholder, replacement in placeholders.items():
        pattern = re.compile(re.escape(placeholder), re.IGNORECASE)
        text = pattern.sub(replacement, text)
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        input_text = request.form["text"]
        module_id = request.form.get("module")  # lấy module được chọn

        # Nếu module_id có giá trị thì ép về int, còn không thì để None
        module_id = int(module_id) if module_id else None


        pre_text, placeholders = preprocess_terms(input_text, module_id)
        translated = translator.translate(pre_text, src="en", dest="vi").text
        result = postprocess_terms(translated, placeholders)
    return render_template("index.html", result=result)

@app.route("/modules")
def modules():
    return render_template("modules.html", modules=range(1, 11))

@app.route("/terms/<int:module_id>")
def terms(module_id):
    terms = get_terms(module_id)
    return render_template("terms.html", module_id=module_id, terms=terms)

if __name__ == "__main__":
    app.run(debug=True)
