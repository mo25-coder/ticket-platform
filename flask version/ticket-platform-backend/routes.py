import sqlite3
from flask import Blueprint, make_response, request, jsonify, session
from flask_mail import Mail, Message
from models import init_db, get_all_events, add_event
from utils import token_required
import qrcode
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

main = Blueprint("main", __name__)
init_db()
DB_PATH = "database.db"
mail = Mail()

@main.route("/events", methods=["GET"])
def list_events():
    # events = get_all_events()
    # get all events from the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, date, location, seats, booked FROM events")
    events = c.fetchall()
    conn.close()
    # format the events into a list of dictionaries
    formatted = [{
        "id": ev[0],
        "name": ev[1],
        "date": ev[2],
        "location": ev[3],
        "seats": ev[4],
        "booked": ev[5]
    } for ev in events]
    return jsonify(formatted)

@main.route("/events", methods=["POST"])
def create_event():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # الحصول على user_id من الجلسة
    user_id = session.get("user_id")
    print(f"User ID from session: {user_id}")

    if not user_id:
        return jsonify({"message": "غير مصرح لك بالدخول"}), 401

    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        return jsonify({"message": "غير مصرح لك بالدخول"}), 401

    data = request.json

    # أولاً نضيف الفعالية إلى جدول events
    c.execute(
        "INSERT INTO events (name, date, location, seats, user_id) VALUES (?, ?, ?, ?, ?)",
        (data["name"], data["date"], data["location"], data["seats"], user_id)
    )
    event_id = c.lastrowid  # نحصل على ID الفعالية اللي أضفناها

    # ثم نولّد المقاعد ونضيفها لجدول seats
    rows, cols = 5, 10
    for r in range(rows):
        for col in range(1, cols + 1):
            seat_label = chr(65 + r) + str(col)
            c.execute("INSERT INTO seats (event_id, seat_label) VALUES (?, ?)", (event_id, seat_label))

    conn.commit()
    conn.close()
    return jsonify({"message": "تم إنشاء الفعالية بنجاح"})

@main.route("/book", methods=["POST"])
@token_required
def book_ticket():
    data = request.json
    event_id = data.get("event_id")
    seat_labels = data.get("seats")  # قائمة مثل ["A1", "A2"]
    user_id = request.user_id

    if not isinstance(seat_labels, list) or not seat_labels:
        return jsonify({"message": "يرجى تحديد المقاعد المطلوبة في قائمة"}), 400

    if len(seat_labels) > 4:
        return jsonify({"message": "لا يمكن حجز أكثر من 4 مقاعد"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # إجمالي المقاعد والمحجوز منها
    c.execute("SELECT seats, booked FROM events WHERE id = ?", (event_id,))
    event_data = c.fetchone()
    if not event_data:
        return jsonify({"message": "الفعالية غير موجودة"}), 404

    total_seats, current_booked = event_data
    remaining = total_seats - current_booked

    if len(seat_labels) > remaining:
        return jsonify({"message": f"عدد المقاعد المتاحة فقط: {remaining}"}), 400

    # المقاعد التي حجزها المستخدم مسبقًا
    c.execute("SELECT SUM(seats_booked) FROM bookings WHERE event_id = ? AND user_id = ?", (event_id, user_id))
    prev_seats = c.fetchone()[0] or 0

    if prev_seats + len(seat_labels) > 4:
        return jsonify({"message": f"لقد حجزت بالفعل {prev_seats} مقاعد. لا يمكنك حجز أكثر من 4."}), 400

    # تحقق من أن المقاعد المطلوبة غير محجوزة
    placeholders = ",".join(["?"] * len(seat_labels))
    query = f"""
        SELECT seat_label FROM seats
        WHERE event_id = ? AND seat_label IN ({placeholders}) AND is_booked = 0
    """
    c.execute(query, [event_id] + seat_labels)
    available = [row[0] for row in c.fetchall()]

    if len(available) != len(seat_labels):
        return jsonify({"message": "بعض المقاعد غير متاحة أو محجوزة بالفعل", "available": available}), 400

    # تسجيل الحجز
    c.execute("INSERT INTO bookings (event_id, user_id, seats_booked) VALUES (?, ?, ?)",
              (event_id, user_id, len(seat_labels)))

    # تحديث جدول المقاعد
    for label in seat_labels:
        c.execute("UPDATE seats SET is_booked = 1, user_id = ? WHERE event_id = ? AND seat_label = ?",
                  (user_id, event_id, label))

    # تحديث عدد المحجوز
    new_booked = current_booked + len(seat_labels)
    c.execute("UPDATE events SET booked = ? WHERE id = ?", (new_booked, event_id))
    remaining_after = total_seats - new_booked

    conn.commit()
    conn.close()

    # return jsonify({
    #     "message": "تم الحجز بنجاح!",
    #     "seats": seat_labels,
    #     "booked_now": len(seat_labels),
    #     "total_booked": new_booked,
    #     "seats_remaining": remaining_after
    # })
    return jsonify({
        "message": "تم الحجز بنجاح!",
        "seats": seat_labels,
        "booked_now": len(seat_labels),
    })
    


@main.route("/seats/<int:event_id>")
def get_seats(event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT seat_label, is_booked FROM seats WHERE event_id = ?", (event_id,))
    # c.execute("SELECT seat_label, is_booked FROM seats WHERE event_id = (SELECT )", (event_id,))
    
    seats = [{"label": row[0], "booked": bool(row[1])} for row in c.fetchall()]
    conn.close()
    return jsonify(seats)

# @main.route("/seats/book", methods=["POST"])
# @token_required
# def book_seats():
#     data = request.json
#     event_id = data.get("event_id")
#     selected_seats = data.get("seats")
#     user_id = request.user_id

#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()

#     placeholders = ",".join("?" * len(selected_seats))
#     query = f"SELECT seat_label FROM seats WHERE event_id = ? AND seat_label IN ({placeholders}) AND is_booked = 0"
#     available = c.execute(query, (event_id, *selected_seats)).fetchall()

#     if len(available) != len(selected_seats):
#         return jsonify({"message": "بعض المقاعد محجوزة بالفعل"}), 400

#     for label in selected_seats:
#         c.execute("UPDATE seats SET is_booked = 1, user_id = ? WHERE event_id = ? AND seat_label = ?",
#                   (user_id, event_id, label))

#     c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
#     user_email = c.fetchone()[0]

#     msg = Message("تأكيد حجزك",
#                   sender="your@email.com",
#                   recipients=[user_email])
#     msg.body = f"تم حجز مقاعدك للفعالية {event_id}:\n" + ", ".join(selected_seats)
#     mail.send(msg)

#     conn.commit()
#     conn.close()
#     return jsonify({"message": "تم حجز المقاعد بنجاح"})

@main.route("/ticket/<int:event_id>", methods=["GET"])
@token_required
def get_ticket(event_id):
    user_id = request.user_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name FROM events WHERE id = ?", (event_id,))
    event_name = c.fetchone()[0]

    c.execute("SELECT seat_label FROM seats WHERE event_id = ? AND user_id = ?", (event_id, user_id))
    seats = [row[0] for row in c.fetchall()]
    if not seats:
        return jsonify({"message": "لا يوجد حجز لك لهذه الفعالية"}), 404

    ticket_data = f"{event_name} - User:{user_id} - Seats:{','.join(seats)}"
    qr = qrcode.make(ticket_data)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return jsonify({
        "event_id": event_id,
        "event_name": event_name,
        "user_id": user_id,
        "seats": seats,
        "qr": qr_b64
    })

@main.route("/ticket/pdf/<int:event_id>")
@token_required
def get_ticket_pdf(event_id):
    user_id = request.user_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name FROM events WHERE id = ?", (event_id,))
    event_name = c.fetchone()[0]

    c.execute("SELECT seat_label FROM seats WHERE event_id = ? AND user_id = ?", (event_id, user_id))
    seats = [row[0] for row in c.fetchall()]
    if not seats:
        return jsonify({"message": "لا يوجد حجز لك لهذه الفعالية"}), 404

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, f"تذكرة حجز الفعالية: {event_name}")
    pdf.drawString(100, 730, f"مستخدم: {user_id}")
    pdf.drawString(100, 710, f"المقاعد المحجوزة: {', '.join(seats)}")
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ticket_{event_id}.pdf'
    return response

@main.route("/admin/bookings", methods=["GET"])
def admin_bookings():
    event_id = request.args.get('event_id')
    user_id = request.args.get('user_id')
    query = """
        SELECT events.name, users.username, seats.seat_label
        FROM seats
        JOIN events ON seats.event_id = events.id
        JOIN users ON seats.user_id = users.id
        WHERE seats.is_booked = 1
    """
    params = []
    if event_id:
        query += " AND events.id = ?"
        params.append(event_id)
    if user_id:
        query += " AND users.id = ?"
        params.append(user_id)
    query += " ORDER BY events.id, users.id"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, tuple(params))
    data = c.fetchall()
    conn.close()

    bookings = [{"event": r[0], "user": r[1], "seat": r[2]} for r in data]
    return jsonify(bookings)

@main.route("/my-events", methods=["GET"])
@token_required
def get_user_events():
    user_id = request.user_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, date, location, seats FROM events WHERE user_id = ?", (user_id,))
    events = [dict(zip(["id", "name", "date", "location", "seats"], row)) for row in c.fetchall()]
    conn.close()
    return jsonify(events)

@main.route("/my-tickets")
@token_required
def my_tickets():
    user_id = request.user_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT events.name, seats.seat_label
        FROM seats
        JOIN events ON seats.event_id = events.id
        WHERE seats.user_id = ? AND seats.is_booked = 1
    """, (user_id,))
    data = c.fetchall()
    conn.close()
    tickets = [{"event": r[0], "seat": r[1]} for r in data]
    return jsonify(tickets)

@main.route("/events/<int:event_id>", methods=["DELETE"])
@token_required
def delete_event(event_id):
    user_id = request.user_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "تم الحذف"})

@main.route("/protected", methods=["GET"])
def protected():
    if "user_id" in session:
        return jsonify({"message": f"أهلاً بيك، المستخدم رقم {session['user_id']}"}), 200
    else:
        return jsonify({"message": "غير مصرح لك بالدخول"}), 401
