#  TheoToDo — Multi-User Task & Operations Management Platform

> A team task management desktop application built with **PyQt5** and **MongoDB**. It allows an admin to assign weekly tasks to employees, track their progress in real time, and manage users securely — all over a Local Area Network (LAN).

***

##  Features

### 🔐 Login & Security
- **Encrypted passwords** — all passwords are hashed with `bcrypt` before being saved to the database; no plain-text passwords are stored
- **First-login warning** — new users are reminded to change their default password when they log in for the first time
- **Role-Based Access Control (RBAC)** — admin and employee accounts have different permissions and see different menus
- **Screen lock** — hides the main window and goes back to the login screen without closing the app
- **Password change** — users can update their password anytime from the sidebar

### 👥 User Management (Admin Only)
- Add new users with a username and password
- Delete users — when a user is deleted, all of their tasks and notes are also removed from the database automatically
- The `admin` account cannot be deleted
- Users cannot delete their own account while they are logged in

### 📅 Weekly Program
- Admin can assign tasks to any user for each day of the week (Monday to Friday)
- Tasks are shown in a table with tabs for each day
- The table **refreshes automatically every 5 seconds** — all users on the same network see updates without restarting the app
- Employees can mark their tasks as completed using checkboxes
- Admin can delete any task from the table

### ✅ My Missions
- Each user can view only their own assigned tasks
- Shows all tasks from all days with their completion status
- A **notification badge** (!) appears on the sidebar button when new tasks are assigned
- The badge disappears automatically once the user opens their task list
- Completion status is saved to the database immediately when a checkbox is clicked

### 📝 Personal Notes
- Users can write, view, and delete their own private notes
- Each note can have a title and a content body
- Notes are sorted by date — newest notes appear at the top
- Notes are private; other users cannot see them

### 🎨 Design & Animations
- Dark theme with a purple accent color (`#6c63ff`)
- Live clock and date shown in the sidebar
- Smooth hover animations on sidebar buttons using `QVariantAnimation`
- The window opens in the center of the screen automatically

***

##  How It Works

### Database — MongoDB (`localhost:27017`)

The app connects to a local MongoDB database. It uses three collections:

| Collection | What it stores |
|---|---|
| `users` | Username, hashed password, first-login flag |
| `tasks` | Weekly tasks grouped by user and day |
| `notes` | Private notes per user with title, content, and date |

When a user is deleted, their tasks and notes are also deleted automatically. This keeps the database clean with no leftover data.

### Who Can Do What

| Feature | Admin | Employee |
|---|---|---|
| View weekly program | ✅ | ✅ |
| Assign tasks to users | ✅ | ❌ |
| Delete tasks | ✅ | ❌ |
| View own missions | ✅ | ✅ |
| Manage users | ✅ | ❌ |
| Write personal notes | ✅ | ✅ |
| Change own password | ✅ | ✅ |
| Lock screen | ✅ | ✅ |

### Real-Time Updates

- The Weekly Program screen checks for new data every **5 seconds**
- The My Missions screen checks every **3 seconds**
- These timers stop when the screen is hidden and start again when it is opened — so the app does not make unnecessary database requests in the background

***

#  Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Desktop UI** | PyQt5 |
| **Database** | MongoDB (PyMongo) |
| **Security** | bcrypt |

***

#  Getting Started

### 1. Install the Required Packages

```bash
pip install pymongo pyqt5 bcrypt
```

### 2. Start MongoDB

Make sure MongoDB is running on your machine at `localhost:27017`.

```bash
# Windows (if installed as a service)
net start MongoDB

# Or start it manually
mongod --dbpath "C:/data/db"
```

### 3. Run the App

```bash
python exe.py
```

When you run the app for the first time, it automatically creates an admin account in the database.

> **Default login:**
> - Username: `admin`
> - Password: `admin`
>
> ⚠️ Please change the admin password right after your first login.

***

## 📂 Project Files

```
theotodo/
├── exe.py              # Main application file
├── logo.png            # Logo shown on the login screen
├── ToDo.ico            # Window icon
├── checked.png         # Checkbox image — checked
├── unchecked.png       # Checkbox image — unchecked
└── README.md
```

***

##  Screens

| Screen | Description |
|---|---|
| **Login** | Enter username and password to access the app |
| **Main Window** | Sidebar menu and content area |
| **Weekly Program** | Assign and view tasks for each day of the week |
| **My Missions** | See your own tasks and mark them as done |
| **Personal Notes** | Write and manage your private notes |
| **User Management** | Add or delete users (admin only) |

***

##  Author

**Teoman Safak Yuksel**
[
