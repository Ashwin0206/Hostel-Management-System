import os, json
from datetime import date, datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Request as HttpRequest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
from .models import User, Attendance, Complaint, Request, Notice, Notification, Worker, FAQ, MealRating
from .models import LostFound, HostelAttendance
from .auth import current_user, allow, verify_password, token_for

Base.metadata.create_all(bind=engine)
app = FastAPI(title="HostelOS API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "https://hostel-management-system-omega-rose.vercel.app"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginIn(BaseModel): email: EmailStr; password: str
class ComplaintIn(BaseModel): title: str = Field(min_length=3,max_length=120); description: str = Field(min_length=5,max_length=2000); location: str = Field(min_length=2,max_length=120)
class ReqIn(BaseModel): kind: str; payload: dict = {}; urgency: str = "NORMAL"
class StatusIn(BaseModel): status: Optional[str] = None; assigned_to: Optional[str] = None
class AttendIn(BaseModel): user_id: Optional[int] = None; status: str = "PRESENT"
class NoticeIn(BaseModel): title: str; body: str; category: str = "General"; hostel: str = "All"
class FAQIn(BaseModel): question: str = Field(min_length=5); answer: str = Field(min_length=5); category: str = "General"; published: bool = True
class MealRatingIn(BaseModel): food_quality: int = Field(ge=1,le=5); taste: int = Field(ge=1,le=5); quantity: int = Field(ge=1,le=5); comment: str = Field(default="", max_length=500)
class ImportStudent(BaseModel): name: str; email: EmailStr; register_number: str = ""; gender: str = ""; block: str; floor: int = Field(ge=1,le=8); room: str
class ImportPreview(BaseModel): students: list[ImportStudent]
class LostFoundIn(BaseModel): kind: str; title: str = Field(min_length=3,max_length=120); description: str = Field(min_length=5,max_length=2000); location: str = Field(min_length=2,max_length=120)
class MarkPresentIn(BaseModel): latitude: float; longitude: float; gps_verified: bool; network_verified: bool

def serial_user(u): return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"hostel":u.hostel,"room":u.room,"block":u.block}
def serial_request(r): return {"id":r.id,"kind":r.kind,"user":serial_user(r.user),"payload":json.loads(r.payload),"status":r.status,"urgency":r.urgency,"created_at":r.created_at.isoformat()}
def serial_lost_found(item): return {"id":item.id,"kind":item.kind,"title":item.title,"description":item.description,"location":item.location,"status":item.status,"user":serial_user(item.user),"created_at":item.created_at.isoformat()}
def notify(db, uid, message): db.add(Notification(user_id=uid,message=message))
def complaint_ai(text):
    v=text.lower(); mapping={"plumb":("Plumbing","HIGH","Maintenance"),"leak":("Plumbing","HIGH","Maintenance"),"electric":("Electrical","HIGH","Maintenance"),"wifi":("Wi-Fi","MEDIUM","IT"),"clean":("Cleaning","MEDIUM","Cleaning"),"security":("Security","HIGH","Security"),"mess":("Mess","MEDIUM","Mess")}
    for k,out in mapping.items():
        if k in v:return {"category":out[0],"priority":out[1],"department":out[2],"summary":"Issue classified from the report details."}
    return {"category":"Room","priority":"MEDIUM","department":"Maintenance","summary":"General room issue requiring review."}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session=Depends(get_db)):
    u=db.query(User).filter(User.email==data.email).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"token":token_for(u),"user":serial_user(u)}
@app.get("/api/auth/me")
def me(user=Depends(current_user)): return serial_user(user)

@app.get("/api/my-room")
def my_room(user=Depends(allow("STUDENT")), db:Session=Depends(get_db)):
    roommates=db.query(User).filter(User.role=="STUDENT",User.hostel==user.hostel,User.room==user.room,User.id!=user.id).order_by(User.id).all()
    return {"room":user.room,"hostel":user.hostel,"block":user.block,"floor":int(user.room[0]) if user.room and user.room[0].isdigit() else None,"occupancy":len(roommates)+1,"roommates":[serial_user(item) for item in roommates]}

@app.get("/api/dashboard")
def dashboard(user=Depends(current_user), db:Session=Depends(get_db)):
    scope = db.query(User).filter(User.role=="STUDENT")
    if user.role=="WARDEN": scope=scope.filter(User.hostel==user.hostel)
    students=scope.all(); ids=[s.id for s in students]
    present=db.query(Attendance).filter(Attendance.user_id.in_(ids),Attendance.date==date.today(),Attendance.status=="PRESENT").count() if ids else 0
    requests=db.query(Request).filter(Request.user_id.in_(ids)) if ids else db.query(Request).filter(False)
    complaints=db.query(Complaint).filter(Complaint.user_id.in_(ids),Complaint.status.not_in(["RESOLVED","COMPLETED"])) if ids else db.query(Complaint).filter(False)
    if user.role=="STUDENT":
        ownreq=db.query(Request).filter(Request.user_id==user.id).order_by(Request.created_at.desc()).all()
        attendance=db.query(Attendance).filter_by(user_id=user.id,date=date.today()).first()
        notices=db.query(Notice).filter((Notice.hostel=="All") | (Notice.hostel==user.hostel) | (Notice.hostel==user.block)).order_by(Notice.created_at.desc()).limit(3).all()
        return {"check_in":{"present":bool(attendance and attendance.status=="PRESENT"),"time":attendance.checked_at.strftime("%I:%M %p") if attendance and attendance.status=="PRESENT" else None},"stats":[{"label":"Active issues","value":db.query(Complaint).filter(Complaint.user_id==user.id,Complaint.status.not_in(["RESOLVED","COMPLETED"])).count()},{"label":"Pending requests","value":sum(x.status in ["PENDING","REQUESTED"] for x in ownreq)}],"requests":[serial_request(x) for x in ownreq[:4]],"announcements":[{"id":n.id,"title":n.title,"body":n.body,"category":n.category,"hostel":n.hostel,"created_at":n.created_at.isoformat()} for n in notices]}
    hospitals=requests.filter(Request.kind=="HOSPITAL",Request.status.in_(["PENDING","APPROVED","ARRANGED"])).order_by(Request.created_at.desc()).all()
    return {"stats":[{"label":"Total students","value":len(students)},{"label":"Present","value":present},{"label":"Not checked in","value":max(len(students)-present,0)},{"label":"On leave","value":requests.filter(Request.kind=="LEAVE",Request.status=="APPROVED").count()},{"label":"Open complaints","value":complaints.count()},{"label":"Pending requests","value":requests.filter(Request.status=="PENDING").count()}],"hospitals":[serial_request(x) for x in hospitals],"insights":[f"{max(len(students)-present,0)} students have not checked in today.",f"{complaints.count()} active issue(s) need operational attention."]}

@app.post("/api/attendance/check-in")
def check_in(http:HttpRequest, user=Depends(allow("STUDENT")), db:Session=Depends(get_db)):
    prefix=os.getenv("HOSTEL_NETWORK_PREFIX","192.168.1."); demo=os.getenv("DEMO_ATTENDANCE_MODE","true").lower()=="true"; ip=http.client.host if http.client else ""
    if not demo and not ip.startswith(prefix): raise HTTPException(403,"Attendance can only be marked from the authorized hostel network")
    existing=db.query(Attendance).filter_by(user_id=user.id,date=date.today()).first()
    if existing and existing.status == "PRESENT": raise HTTPException(409,"You have already checked in for this attendance period")
    if existing: existing.status = "PRESENT"; existing.checked_at = datetime.utcnow()
    else: db.add(Attendance(user_id=user.id,date=date.today(),status="PRESENT"))
    db.commit()
    return {"message":"Present recorded", "verified_network": demo or ip.startswith(prefix), "time":datetime.now().strftime("%I:%M %p")}
@app.get("/api/attendance/room/{room}")
def room_attendance(room:str, user=Depends(allow("WARDEN","ADMIN")), db:Session=Depends(get_db)):
    q=db.query(User).filter(User.room==room,User.role=="STUDENT")
    # A room number may exist in both hostels; wardens must never see the other hostel.
    if user.role=="WARDEN": q=q.filter(User.hostel==user.hostel)
    students=q.all()
    return [{**serial_user(s),"status":(db.query(Attendance).filter_by(user_id=s.id,date=date.today()).first() or type("x",(),{"status":"ABSENT"})()).status} for s in students]
@app.post("/api/attendance/mark")
def mark_attendance(data:AttendIn, user=Depends(allow("WARDEN","ADMIN")), db:Session=Depends(get_db)):
    target=db.get(User,data.user_id)
    if not target or target.role!="STUDENT": raise HTTPException(404,"Student not found")
    if user.role=="WARDEN" and target.hostel!=user.hostel: raise HTTPException(403,"Student belongs to another hostel")
    rec=db.query(Attendance).filter_by(user_id=target.id,date=date.today()).first()
    if rec: rec.status=data.status
    else: db.add(Attendance(user_id=target.id,date=date.today(),status=data.status))
    db.commit(); return {"message":"Attendance saved"}

@app.get("/api/complaints")
def complaints(user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Complaint).order_by(Complaint.created_at.desc())
    if user.role=="STUDENT":q=q.filter(Complaint.user_id==user.id)
    elif user.role=="WARDEN":q=q.join(User).filter(User.hostel==user.hostel)
    return [{"id":x.id,"ticket":x.ticket,"title":x.title,"category":x.category,"priority":x.priority,"status":x.status,"assigned_to":x.assigned_to,"location":x.location,"student":x.user.name,"created_at":x.created_at.isoformat()} for x in q.all()]
@app.post("/api/complaints")
def create_complaint(data:ComplaintIn,user=Depends(allow("STUDENT")),db:Session=Depends(get_db)):
    ai=complaint_ai(data.title+" "+data.description); c=Complaint(ticket=f"CMP-{date.today().year}-{db.query(Complaint).count()+1:04d}",user_id=user.id,title=data.title,description=data.description,location=data.location,category=ai["category"],priority=ai["priority"])
    db.add(c); notify(db,user.id,f"Complaint {c.ticket} created and routed to {ai['department']}.")
    for warden in db.query(User).filter(User.role=="WARDEN",User.hostel==user.hostel): notify(db,warden.id,f"New {ai['priority'].lower()} complaint {c.ticket} from {user.name}.")
    for manager in db.query(User).filter(User.role=="STAFF_MANAGER"): notify(db,manager.id,f"New maintenance task {c.ticket} requires assignment.")
    db.commit(); return {"ticket":c.ticket,"analysis":ai}
@app.patch("/api/complaints/{cid}")
def update_complaint(cid:int,data:StatusIn,user=Depends(allow("WARDEN","STAFF_MANAGER","ADMIN")),db:Session=Depends(get_db)):
    c=db.get(Complaint,cid)
    if not c:raise HTTPException(404,"Complaint not found")
    if user.role=="WARDEN" and c.user.hostel!=user.hostel: raise HTTPException(403,"Complaint belongs to another hostel")
    if data.status:
        c.status=data.status
        notify(db,c.user_id,f"Complaint {c.ticket} is now {data.status}.")
    if data.assigned_to is not None:
        c.assigned_to=data.assigned_to or None
        if c.assigned_to:
            for manager in db.query(User).filter(User.role=="STAFF_MANAGER"): notify(db,manager.id,f"Complaint {c.ticket} was assigned to {c.assigned_to}.")
            notify(db,c.user_id,f"Complaint {c.ticket} was assigned to {c.assigned_to}.")
    db.commit();return {"message":"Complaint updated"}

@app.get("/api/requests")
def get_requests(kind:Optional[str]=None,user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Request).order_by(Request.created_at.desc())
    if kind:q=q.filter(Request.kind==kind)
    if user.role=="STUDENT":q=q.filter(Request.user_id==user.id)
    elif user.role=="WARDEN":q=q.join(User).filter(User.hostel==user.hostel)
    return [serial_request(x) for x in q.all()]
@app.post("/api/requests")
def create_request(data:ReqIn,user=Depends(allow("STUDENT")),db:Session=Depends(get_db)):
    kinds={"LEAVE","OUTPASS","CLEANING","HOSPITAL"}
    if data.kind not in kinds:raise HTTPException(400,"Unsupported request")
    r=Request(kind=data.kind,user_id=user.id,payload=json.dumps(data.payload),urgency=data.urgency,status="REQUESTED" if data.kind=="OUTPASS" else "PENDING")
    db.add(r); notify(db,user.id,f"Your {data.kind.lower()} request has been submitted.")
    for warden in db.query(User).filter(User.role=="WARDEN",User.hostel==user.hostel): notify(db,warden.id,f"New {data.kind.lower()} request from {user.name} requires review.")
    db.commit();return serial_request(r)
@app.patch("/api/requests/{rid}")
def update_request(rid:int,data:StatusIn,user=Depends(allow("WARDEN","STAFF_MANAGER","ADMIN")),db:Session=Depends(get_db)):
    r=db.get(Request,rid)
    if not r:raise HTTPException(404,"Request not found")
    if user.role=="WARDEN" and r.user.hostel!=user.hostel: raise HTTPException(403,"Request belongs to another hostel")
    r.status=data.status;notify(db,r.user_id,f"Your {r.kind.lower()} request is now {data.status}.");db.commit();return serial_request(r)

@app.get("/api/notices")
def notices(user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Notice)
    if user.role in ("STUDENT","WARDEN"): q=q.filter((Notice.hostel=="All") | (Notice.hostel==user.hostel) | (Notice.hostel==user.block))
    return [{"id":x.id,"title":x.title,"body":x.body,"category":x.category,"hostel":x.hostel,"created_at":x.created_at.isoformat()} for x in q.order_by(Notice.created_at.desc()).all()]
@app.post("/api/notices")
def add_notice(data:NoticeIn,user=Depends(allow("WARDEN","ADMIN")),db:Session=Depends(get_db)):
    n=Notice(**data.model_dump());db.add(n)
    recipients=db.query(User).filter(User.role=="STUDENT").all()
    for recipient in recipients:
        if n.hostel in ("All",recipient.hostel,recipient.block): notify(db,recipient.id,f"New {n.category.lower()} announcement: {n.title}")
    db.commit();return {"message":"Notice published"}
@app.get("/api/notifications")
def notifications(user=Depends(current_user),db:Session=Depends(get_db)):return [{"id":x.id,"message":x.message,"read":x.read,"created_at":x.created_at.isoformat()} for x in db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()]
@app.get("/api/workers")
def workers(user=Depends(allow("WARDEN","STAFF_MANAGER","ADMIN")),db:Session=Depends(get_db)):return [{"id":x.id,"name":x.name,"department":x.department,"job":x.job,"phone":x.phone,"active":x.active} for x in db.query(Worker).all()]

@app.get("/api/students")
def students(user=Depends(allow("WARDEN","ADMIN")),db:Session=Depends(get_db)):
    q=db.query(User).filter(User.role=="STUDENT")
    if user.role=="WARDEN": q=q.filter(User.hostel==user.hostel)
    return [serial_user(item) for item in q.order_by(User.room,User.name).all()]

@app.get("/api/lost-found")
def lost_found(user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(LostFound).join(User).order_by(LostFound.created_at.desc())
    if user.role=="STUDENT": q=q.filter(User.hostel==user.hostel)
    elif user.role=="WARDEN": q=q.filter(User.hostel==user.hostel)
    return [serial_lost_found(item) for item in q.all()]

@app.post("/api/lost-found")
def create_lost_found(data:LostFoundIn,user=Depends(allow("STUDENT")),db:Session=Depends(get_db)):
    if data.kind not in ("LOST","FOUND"): raise HTTPException(400,"Kind must be LOST or FOUND")
    item=LostFound(**data.model_dump(),user_id=user.id)
    db.add(item)
    for warden in db.query(User).filter(User.role=="WARDEN",User.hostel==user.hostel): notify(db,warden.id,f"New {data.kind.lower()} item reported by {user.name}.")
    db.commit(); return serial_lost_found(item)

@app.patch("/api/lost-found/{item_id}")
def update_lost_found(item_id:int,data:StatusIn,user=Depends(allow("WARDEN","ADMIN")),db:Session=Depends(get_db)):
    item=db.get(LostFound,item_id)
    if not item: raise HTTPException(404,"Lost and found item not found")
    if user.role=="WARDEN" and item.user.hostel!=user.hostel: raise HTTPException(403,"Item belongs to another hostel")
    if data.status: item.status=data.status
    notify(db,item.user_id,f"Your {item.kind.lower()} item is now {item.status.lower()}.")
    db.commit(); return serial_lost_found(item)

@app.get("/api/analytics")
def analytics(user=Depends(allow("ADMIN","WARDEN")),db:Session=Depends(get_db)):
    student_query=db.query(User).filter(User.role=="STUDENT")
    if user.role=="WARDEN": student_query=student_query.filter(User.hostel==user.hostel)
    students=student_query.all(); student_ids=[item.id for item in students]
    def grouped(query, column): return [{"label":str(label or "Unknown"),"value":count} for label,count in query.with_entities(column,func.count()).group_by(column).order_by(column).all()]
    attendance=db.query(Attendance).filter(Attendance.user_id.in_(student_ids),Attendance.date==date.today(),Attendance.status=="PRESENT").count() if student_ids else 0
    requests=db.query(Request).filter(Request.user_id.in_(student_ids)) if student_ids else db.query(Request).filter(False)
    complaints_q=db.query(Complaint).filter(Complaint.user_id.in_(student_ids)) if student_ids else db.query(Complaint).filter(False)
    return {"students":len(students),"attendance":{"present":attendance,"not_checked_in":max(len(students)-attendance,0)},"complaints":{"by_category":grouped(complaints_q,Complaint.category),"by_status":grouped(complaints_q,Complaint.status)},"requests":{"by_type":grouped(requests,Request.kind),"hospital":requests.filter(Request.kind=="HOSPITAL").count(),"leave":requests.filter(Request.kind=="LEAVE").count(),"outpass":requests.filter(Request.kind=="OUTPASS").count(),"cleaning":requests.filter(Request.kind=="CLEANING").count()},"meal_ratings":{"count":db.query(MealRating).count(),"average":round(float(db.query(func.avg((MealRating.food_quality+MealRating.taste+MealRating.quantity)/3)).scalar() or 0),1)}}

@app.get("/api/faqs")
def faqs(category: Optional[str]=None, user=Depends(current_user), db:Session=Depends(get_db)):
    q=db.query(FAQ).filter(FAQ.published==True)
    if category and category!="All": q=q.filter(FAQ.category==category)
    return [{"id":x.id,"question":x.question,"answer":x.answer,"category":x.category} for x in q.order_by(FAQ.category,FAQ.id).all()]
@app.post("/api/faqs")
def create_faq(data:FAQIn,user=Depends(allow("WARDEN","ADMIN")),db:Session=Depends(get_db)):
    f=FAQ(**data.model_dump());db.add(f);db.commit();return {"id":f.id,"message":"FAQ saved"}
@app.delete("/api/faqs/{fid}")
def delete_faq(fid:int,user=Depends(allow("WARDEN","ADMIN")),db:Session=Depends(get_db)):
    f=db.get(FAQ,fid)
    if not f: raise HTTPException(404,"FAQ not found")
    db.delete(f);db.commit();return {"message":"FAQ deleted"}

@app.post("/api/mess/ratings")
def rate_previous_meal(data:MealRatingIn,user=Depends(allow("STUDENT")),db:Session=Depends(get_db)):
    rating=MealRating(user_id=user.id,meal_name="Lunch",**data.model_dump());db.add(rating);db.commit();return {"message":"Previous meal rating recorded"}
@app.get("/api/mess/summary")
def mess_summary(user=Depends(current_user),db:Session=Depends(get_db)):
    avg=db.query(func.avg((MealRating.food_quality+MealRating.taste+MealRating.quantity)/3)).scalar()
    return {"average_rating":round(float(avg or 0),1),"rating_count":db.query(MealRating).count(),"previous_meal":"Lunch"}

@app.post("/api/admin/import/students/preview")
def preview_students(data:ImportPreview,user=Depends(allow("ADMIN")),db:Session=Depends(get_db)):
    issues=[]; seen=set()
    for i,s in enumerate(data.students,1):
        if s.email in seen or db.query(User).filter_by(email=s.email).first():issues.append({"row":i,"issue":"Duplicate email"})
        seen.add(s.email)
        if not s.room.strip(): issues.append({"row":i,"issue":"Missing room assignment"})
    return {"detected":len(data.students),"valid":len(data.students)-len(issues),"issues":issues}
@app.post("/api/admin/import/students")
def import_students(data:ImportPreview,user=Depends(allow("ADMIN")),db:Session=Depends(get_db)):
    preview=preview_students(data,user,db)
    if preview["issues"]: raise HTTPException(422,{"message":"Resolve validation issues before import","issues":preview["issues"]})
    from .auth import hash_password
    for s in data.students: db.add(User(name=s.name,email=s.email,password_hash=hash_password("Welcome@123"),role="STUDENT",hostel="Girls Hostel" if s.gender.lower().startswith("f") else "Boys Hostel",room=s.room,block=s.block))
    db.commit();return {"message":f"Imported {len(data.students)} students"}

# ============================================================
# HOSTEL ATTENDANCE VERIFICATION MODULE
# ============================================================
import math as _math

def _ist_now():
    """Return current datetime in IST (UTC+5:30)."""
    from datetime import timezone, timedelta
    tz_ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(tz_ist)

def _session_state():
    """Return 'before' | 'open' | 'closed' based on IST server time."""
    now = _ist_now()
    if now.hour < 16: return "before"
    if now.hour < 18: return "open"
    return "closed"

def _haversine_m(lat1, lon1, lat2, lon2):
    """Distance in metres between two GPS coordinates."""
    R = 6_371_000
    phi1, phi2 = _math.radians(lat1), _math.radians(lat2)
    dphi = _math.radians(lat2 - lat1)
    dlam = _math.radians(lon2 - lon1)
    a = _math.sin(dphi/2)**2 + _math.cos(phi1)*_math.cos(phi2)*_math.sin(dlam/2)**2
    return R * 2 * _math.atan2(_math.sqrt(a), _math.sqrt(1-a))

def _hostel_config():
    return {
        "lat": float(os.getenv("HOSTEL_LAT", "20.5937")),
        "lon": float(os.getenv("HOSTEL_LON", "78.9629")),
        "geofence_meters": int(os.getenv("HOSTEL_GEOFENCE_METERS", "100")),
        "network_prefix": os.getenv("HOSTEL_NETWORK_PREFIX", "192.168.1."),
        "demo_mode": os.getenv("DEMO_ATTENDANCE_MODE", "true").lower() == "true",
    }

def _today_record(user_id, db):
    return db.query(HostelAttendance).filter_by(user_id=user_id, date=date.today()).first()

@app.get("/api/hostel-attendance/config")
def ha_config(user=Depends(current_user)):
    cfg = _hostel_config()
    return {"hostel_lat": cfg["lat"], "hostel_lon": cfg["lon"],
            "geofence_meters": cfg["geofence_meters"], "demo_mode": cfg["demo_mode"],
            "session_start": "16:00", "session_end": "18:00",
            "session_state": _session_state()}

@app.get("/api/hostel-attendance/status")
def ha_status(user=Depends(allow("STUDENT")), db: Session=Depends(get_db)):
    rec = _today_record(user.id, db)
    state = _session_state()
    status = rec.status if rec else ("ABSENT" if state == "closed" else "PENDING")
    return {
        "session_state": state,
        "status": status,
        "already_marked": bool(rec and rec.status == "PRESENT"),
        "marked_time": rec.marked_time.strftime("%I:%M %p") if rec and rec.marked_time else None,
        "gps_verified": rec.gps_verified if rec else False,
        "network_verified": rec.network_verified if rec else False,
    }

@app.post("/api/hostel-attendance/verify-network")
def ha_verify_network(http: HttpRequest, user=Depends(allow("STUDENT"))):
    cfg = _hostel_config()
    if cfg["demo_mode"]: return {"network_verified": True, "demo_mode": True, "message": "Demo mode — network check bypassed."}
    ip = http.client.host if http.client else ""
    ok = ip.startswith(cfg["network_prefix"])
    return {"network_verified": ok, "demo_mode": False,
            "message": "Connected to approved hostel network." if ok else "Please connect to the approved hostel Wi-Fi."}

@app.post("/api/hostel-attendance/mark-present")
def ha_mark_present(data: MarkPresentIn, http: HttpRequest, user=Depends(allow("STUDENT")), db: Session=Depends(get_db)):
    cfg = _hostel_config()
    state = _session_state()
    if state != "open":
        raise HTTPException(403, "Attendance session is not open. Session runs from 4:00 PM to 6:00 PM.")
    # Duplicate check
    existing = _today_record(user.id, db)
    if existing and existing.status == "PRESENT":
        raise HTTPException(409, "Attendance already marked as PRESENT for today.")
    # Server-side GPS validation
    gps_ok = True
    if not cfg["demo_mode"]:
        dist = _haversine_m(data.latitude, data.longitude, cfg["lat"], cfg["lon"])
        if dist > cfg["geofence_meters"]:
            raise HTTPException(403, f"You are outside the permitted hostel location (distance: {dist:.0f}m, allowed: {cfg['geofence_meters']}m).")
        gps_ok = data.gps_verified
    # Server-side network validation
    net_ok = True
    if not cfg["demo_mode"]:
        ip = http.client.host if http.client else ""
        net_ok = ip.startswith(cfg["network_prefix"])
        if not net_ok:
            raise HTTPException(403, "Please connect to the approved hostel Wi-Fi to mark attendance.")
    now_ist = _ist_now()
    if existing:
        existing.status = "PRESENT"; existing.marked_time = now_ist
        existing.gps_verified = True; existing.network_verified = True
        existing.latitude = data.latitude; existing.longitude = data.longitude
        existing.ip_address = http.client.host if http.client else ""
    else:
        db.add(HostelAttendance(
            user_id=user.id, date=date.today(), status="PRESENT",
            marked_time=now_ist, gps_verified=True, network_verified=True,
            latitude=data.latitude, longitude=data.longitude,
            ip_address=http.client.host if http.client else ""
        ))
    notify(db, user.id, f"Hostel attendance marked PRESENT at {now_ist.strftime('%I:%M %p')} on {date.today().strftime('%d %b %Y')}.")
    db.commit()
    return {"message": "Attendance marked PRESENT", "time": now_ist.strftime("%I:%M %p"),
            "gps_verified": True, "network_verified": True, "status": "PRESENT"}

@app.get("/api/hostel-attendance/summary")
def ha_summary(user=Depends(allow("WARDEN", "ADMIN")), db: Session=Depends(get_db)):
    q = db.query(User).filter(User.role == "STUDENT")
    if user.role == "WARDEN": q = q.filter(User.hostel == user.hostel)
    students = q.order_by(User.room, User.name).all()
    state = _session_state()
    total = len(students)
    present_rows, absent_rows, pending_rows = [], [], []
    for s in students:
        rec = db.query(HostelAttendance).filter_by(user_id=s.id, date=date.today()).first()
        if rec and rec.status == "PRESENT":
            present_rows.append({"id": s.id, "name": s.name, "room": s.room or "",
                "email": s.email, "status": "PRESENT",
                "marked_time": rec.marked_time.strftime("%I:%M %p") if rec.marked_time else "—",
                "gps_verified": rec.gps_verified, "network_verified": rec.network_verified})
        elif state == "closed" and (not rec or rec.status != "PRESENT"):
            absent_rows.append({"id": s.id, "name": s.name, "room": s.room or "",
                "email": s.email, "status": "ABSENT",
                "reason": "Verification Failed" if rec else "Attendance Not Marked"})
        else:
            pending_rows.append({"id": s.id, "name": s.name, "room": s.room or "",
                "email": s.email, "status": "PENDING"})
    return {"session_state": state, "total": total,
            "present_count": len(present_rows), "pending_count": len(pending_rows),
            "absent_count": len(absent_rows),
            "present": present_rows, "absent": absent_rows, "pending": pending_rows}

@app.post("/api/hostel-attendance/notify-absent")
def ha_notify_absent(data: dict, user=Depends(allow("WARDEN", "ADMIN")), db: Session=Depends(get_db)):
    student_id = data.get("student_id")
    if not student_id: raise HTTPException(400, "student_id required")
    target = db.get(User, student_id)
    if not target or target.role != "STUDENT": raise HTTPException(404, "Student not found")
    if user.role == "WARDEN" and target.hostel != user.hostel: raise HTTPException(403, "Student belongs to another hostel")
    state = _session_state()
    if state == "open":
        msg = "Hostel attendance is open from 4:00 PM to 6:00 PM. Please enable location and connect to the approved hostel Wi-Fi."
    else:
        msg = "Your hostel attendance was not marked before the attendance session closed."
    notify(db, student_id, msg)
    db.commit()
    return {"message": f"Notification sent to {target.name}"}

@app.post("/api/hostel-attendance/session-close")
def ha_session_close(user=Depends(allow("WARDEN", "ADMIN")), db: Session=Depends(get_db)):
    """Mark all PENDING records as ABSENT and notify students and warden."""
    state = _session_state()
    if state != "closed": raise HTTPException(400, "Session has not closed yet (before 6:00 PM).")
    q = db.query(User).filter(User.role == "STUDENT")
    if user.role == "WARDEN": q = q.filter(User.hostel == user.hostel)
    students = q.all(); absent_count = 0; present_count = 0
    for s in students:
        rec = db.query(HostelAttendance).filter_by(user_id=s.id, date=date.today()).first()
        if rec and rec.status == "PRESENT": present_count += 1; continue
        if not rec:
            db.add(HostelAttendance(user_id=s.id, date=date.today(), status="ABSENT"))
        elif rec.status == "PENDING":
            rec.status = "ABSENT"
        notify(db, s.id, "Your hostel attendance was not marked before the attendance session closed.")
        absent_count += 1
    notify(db, user.id, f"Attendance session completed. Present: {present_count}, Absent: {absent_count}.")
    db.commit()
    return {"message": "Session closed", "present": present_count, "absent": absent_count}
