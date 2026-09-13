from .database import Base, engine, SessionLocal
from .models import FAQ, User, Worker
from .auth import hash_password


def add_user(db, name, email, role, hostel="Boys Hostel", room=None, block=None):
    return User(
        name=name,
        email=email,
        password_hash=hash_password("Demo@123"),
        role=role,
        hostel=hostel,
        room=room,
        block=block,
    )


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    users = [
        add_user(db, "Ashwin Kumar", "student1@demo.hostelos", "STUDENT", "Boys Hostel", "101", "B"),
        add_user(db, "Rahul S", "student2@demo.hostelos", "STUDENT", "Boys Hostel", "101", "B"),
        add_user(db, "Arun Prakash", "student3@demo.hostelos", "STUDENT", "Boys Hostel", "101", "B"),
        add_user(db, "Meera Nair", "student4@demo.hostelos", "STUDENT", "Boys Hostel", "101", "B"),
        add_user(db, "Boys Warden", "boys.warden@demo.hostelos", "WARDEN", "Boys Hostel"),
        add_user(db, "Girls Warden", "girls.warden@demo.hostelos", "WARDEN", "Girls Hostel"),
        add_user(db, "Priya Supervisor", "staff@demo.hostelos", "STAFF_MANAGER"),
        add_user(db, "College Administration", "admin@demo.hostelos", "ADMIN"),
    ]

    # Master dataset only: 4 floors, 40 rooms, 4 residents per room.
    base_hash = hash_password("Demo@123")
    first = ["Aarav", "Vihaan", "Aditya", "Arjun", "Kabir", "Ishaan", "Rohan", "Dev", "Kunal", "Nikhil"]
    last = ["Sharma", "Reddy", "Patel", "Kumar", "Nair", "Singh", "Das", "Menon", "Gupta", "Verma"]
    index = 0
    for floor in range(1, 5):
        hostel, block = ("Boys Hostel", "B") if floor < 3 else ("Girls Hostel", "G")
        for number in range(1, 11):
            room = f"{floor}{number:02d}"
            if room == "101":
                continue
            for _ in range(4):
                name = f"{first[index % len(first)]} {last[(index // len(first)) % len(last)]}"
                users.append(User(
                    name=name,
                    email=f"student{index + 5}@demo.hostelos",
                    password_hash=base_hash,
                    role="STUDENT",
                    hostel=hostel,
                    room=room,
                    block=block,
                ))
                index += 1

    db.add_all(users)
    db.add_all([
        Worker(name="Ramesh Kumar", department="Maintenance", job="Plumber", phone="90000 12345"),
        Worker(name="Lakshmi Devi", department="Cleaning", job="Cleaning supervisor", phone="90000 23456"),
        Worker(name="Sanjay Patel", department="Security", job="Security supervisor", phone="90000 34567"),
        FAQ(question="How do I check in?", answer="Open Attendance and check in from the authorized hostel network.", category="Attendance"),
        FAQ(question="How do I request leave?", answer="Open Requests, choose Leave, complete the form, and submit it for review.", category="Leave"),
        FAQ(question="How do I request an out pass?", answer="Open Out Pass and provide the destination, date, and reason.", category="Out Pass"),
        FAQ(question="How are hospital visits handled?", answer="Submit a Hospital request and wait for the warden to review it.", category="Hospital"),
        FAQ(question="Where can I find hostel rules?", answer="Hostel rules and operational guidance are listed in this FAQ area.", category="Hostel Rules"),
    ])
    db.commit()
    db.close()
    print("HostelOS master database seeded with zero operational activity.")


if __name__ == "__main__":
    run()
