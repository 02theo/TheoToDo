import sys
from pymongo import MongoClient
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QMainWindow, QSpacerItem, QSizePolicy, QCheckBox, QTabWidget,
    QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QListWidget, QListWidgetItem, QDialog, QFrame,
    QDesktopWidget, QInputDialog
)
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QFont, QPixmap, QPalette
from datetime import datetime
from bson.objectid import ObjectId
from PyQt5.QtGui import QIcon
import bcrypt

# MongoDB bağlantısı
client = MongoClient("mongodb://localhost:27017/")
db = client["gorevUygulamasi"]
users_collection = db["users"]
tasks_collection = db["tasks"]
notes_collection = db["notes"]

# Admin kullanıcısının varlığını kontrol et ve gerekirse oluştur
# Artık şifre hashlenmiş olarak kontrol ediliyor ve ekleniyor
if not users_collection.find_one({"_id": "admin"}):
    hashed_password = bcrypt.hashpw(b"admin", bcrypt.gensalt())
    users_collection.insert_one({
        "_id": "admin",
        "password": hashed_password.decode('utf-8'),
        "is_first_login": False,
        "seen": False
    })

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giriş Ekranı")
        self.setGeometry(100, 100, 512, 256)
        self.setFixedSize(512, 256)
        self.setWindowIcon(QIcon('ToDo.ico'))
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Giriş")

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
                font-family: Arial;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #2d2d44;
                border: 1px solid #3d3d5c;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #6c63ff;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a73ff;
            }
            QLabel {
                color: #ffffff;
            }
            /* QMessageBox Button Styling */
            QMessageBox QPushButton {
                background-color: #6c63ff; /* Main accent color for buttons */
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #7a73ff;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)

        logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        layout.addWidget(QLabel("Kullanıcı Adı:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Şifre:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)
        self.login_button.clicked.connect(self.check_login)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text().encode('utf-8') # Şifreyi byte dizisine çevir

        user = users_collection.find_one({"_id": username})

        if user:
            # Hashlenmiş şifreyi kontrol et
            try:
                hashed_password = user["password"].encode('utf-8')
                if bcrypt.checkpw(password, hashed_password):
                    self.main_window = MainWindow(username, self)
                    self.main_window.show()
                    self.hide()
                    if user.get("is_first_login"):
                        QMessageBox.information(self, "Uyarı", "İlk kez giriş yapıyorsunuz. Güvenliğiniz için şifrenizi değiştirmeniz önerilir.")
                        users_collection.update_one({"_id": username}, {"$set": {"is_first_login": False}})
                else:
                    QMessageBox.warning(self, "Hata", "Geçersiz Kullanıcı Adı veya Şifre")
            except:
                # Eğer şifre hashlenmemişse (eski veritabanı için)
                QMessageBox.warning(self, "Hata", "Kullanıcı verisi bozuk veya eski. Lütfen yöneticinizle iletişime geçin.")
        else:
            QMessageBox.warning(self, "Hata", "Geçersiz Kullanıcı Adı veya Şifre")

class MainWindow(QMainWindow):
    def __init__(self, username, login_window_instance):
        super().__init__()
        self.current_user = username
        self.login_window = login_window_instance
        self.setWindowTitle("TheoToDo")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon('ToDo.ico'))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)

        self.sidebar_layout = QVBoxLayout()
        self.content_layout = QVBoxLayout()

        self.init_styles()
        self.init_sidebar()
        self.init_content_area()
        
        self.main_layout.addLayout(self.sidebar_layout, 1)
        self.main_layout.addLayout(self.content_layout, 4)

        self.update_time_and_date()
        self.check_unseen_tasks()
        self.center()
        self.show_weekly_program()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2f;
                color: #ffffff;
                font-family: Arial;
            }
            QFrame#ClockFrame {
                background-color: #2d2d44;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel#ClockLabel, QLabel#DateLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 15px;
                color: #ffffff;
                font-size: 16px;
                text-align: left;
                padding-left: 20px;
                margin-bottom: 5px;
            }
            /* Default button background for animation */
            QPushButton[animated="true"] {
                background-color: #2d2d44; 
            }
            QPushButton[animated="true"]:hover {
                background-color: #3d3d5c;
            }
            QPushButton#LogoutButton[animated="true"] {
                background-color: #e74c3c;
                font-weight: bold;
            }
            QPushButton#LogoutButton[animated="true"]:hover {
                background-color: #c0392b;
            }

            QLabel#MissionNotification {
                background-color: red;
                border-radius: 7px;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
                color: white;
                font-size: 10px;
                text-align: center;
                vertical-align: middle;
                margin-left: 5px;
            }
            /* QMessageBox Button Styling */
            QMessageBox QPushButton {
                background-color: #6c63ff; /* Main accent color for buttons */
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #7a73ff;
            }
            QDialog QPushButton {
                background-color: #6c63ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
        """)

    def init_sidebar(self):
        # Saat ve Tarih Alanı
        clock_frame = QFrame(self)
        clock_frame.setObjectName("ClockFrame")
        clock_frame.setLayout(QVBoxLayout())
        
        self.clock_label = QLabel()
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(Qt.AlignCenter)
        clock_frame.layout().addWidget(self.clock_label)

        self.date_label = QLabel()
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignCenter)
        clock_frame.layout().addWidget(self.date_label)
        
        self.sidebar_layout.addWidget(clock_frame)
        self.sidebar_layout.addSpacing(20)

        # Hoş Geldiniz Mesajı
        welcome_label = QLabel(f"Hoş Geldiniz, {self.current_user}!")
        welcome_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #6c63ff;")
        self.sidebar_layout.addWidget(welcome_label)

        # Butonlar
        self.weekly_program_button = QPushButton("Haftalık Program")
        self.notes_button = QPushButton("Özel Notlar")
        self.missions_button = QPushButton("Görevlerim")
        self.user_management_button = QPushButton("Kullanıcı Yönetimi")
        
        self.change_password_button = QPushButton("Şifre Değiştir")
        
        self.lock_screen_button = QPushButton("Ekranı Kilitle")
        self.logout_button = QPushButton("Çıkış Yap")
        self.logout_button.setObjectName("LogoutButton")

        # Set property for animation
        for btn in [self.weekly_program_button, self.notes_button, self.missions_button, 
                    self.user_management_button, self.change_password_button, self.lock_screen_button, self.logout_button]:
            btn.setProperty("animated", True)


        
        missions_button_layout = QHBoxLayout()
        missions_button_layout.addWidget(self.missions_button)
        self.mission_notification = QLabel()
        self.mission_notification.setObjectName("MissionNotification")
        self.mission_notification.setVisible(False)
        self.mission_notification.setText("!")
        missions_button_layout.addWidget(self.mission_notification)
        missions_button_layout.addStretch(1)

        self.sidebar_layout.addWidget(self.weekly_program_button)
        self.sidebar_layout.addWidget(self.notes_button)
        self.sidebar_layout.addLayout(missions_button_layout)

        if self.current_user == "admin":
            self.sidebar_layout.addWidget(self.user_management_button)
            
        self.sidebar_layout.addWidget(self.change_password_button)
        
        self.sidebar_layout.addWidget(self.lock_screen_button)
        self.sidebar_layout.addStretch(1)
        self.sidebar_layout.addWidget(self.logout_button)

        # Butonlara bağlantılar
        self.weekly_program_button.clicked.connect(self.show_weekly_program)
        self.notes_button.clicked.connect(self.show_notes)
        self.missions_button.clicked.connect(self.show_missions)
        if self.current_user == "admin":
            self.user_management_button.clicked.connect(self.show_user_management)
        
        self.change_password_button.clicked.connect(self.change_password)
        
        self.lock_screen_button.clicked.connect(self.lock_screen)
        self.logout_button.clicked.connect(self.logout)

        for btn in [self.weekly_program_button, self.notes_button, self.missions_button, 
                    self.user_management_button if self.current_user == "admin" else None,
                    self.change_password_button,
                    self.lock_screen_button]:
            if btn:
                btn.installEventFilter(self)
        self.logout_button.installEventFilter(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_and_date)
        self.timer.start(1000)
    
    def change_password(self):
        new_password, ok = QInputDialog.getText(self, "Şifre Değiştir", "Yeni şifrenizi girin:", QLineEdit.Password)
        if ok and new_password:
            confirm_password, ok = QInputDialog.getText(self, "Şifre Değiştir", "Yeni şifrenizi tekrar girin:", QLineEdit.Password)
            if ok and confirm_password:
                if new_password == confirm_password:
                    try:
                        # Yeni şifreyi hashle
                        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                        users_collection.update_one(
                            {"_id": self.current_user},
                            {"$set": {"password": hashed_password.decode('utf-8')}}
                        )
                        QMessageBox.information(self, "Başarılı", "Şifreniz başarıyla değiştirildi.")
                    except Exception as e:
                        QMessageBox.critical(self, "Hata", f"Şifre değiştirilirken bir hata oluştu: {e}")
                else:
                    QMessageBox.warning(self, "Hata", "Girdiğiniz şifreler eşleşmiyor.")


    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Enter:
                self.start_button_animation(obj, QColor("#6c63ff") if obj.objectName() != "LogoutButton" else QColor("#c0392b"))
            elif event.type() == QEvent.Leave:
                self.start_button_animation(obj, QColor("#2d2d44") if obj.objectName() != "LogoutButton" else QColor("#e74c3c"))
        return super().eventFilter(obj, event)

    def start_button_animation(self, button, target_color):
        current_color = button.palette().color(QPalette.Button) 

        if hasattr(button, '_animation') and button._animation.state() == QVariantAnimation.Running:
            button._animation.stop()

        button._animation = QVariantAnimation()
        button._animation.setDuration(200)
        button._animation.setStartValue(current_color)
        button._animation.setEndValue(target_color)
        
        button._animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        button._animation.valueChanged.connect(lambda color: self.set_button_background(button, color))
        
        button._animation.start()

    def set_button_background(self, button, color):
        button.setStyleSheet(f"""
            QPushButton[animated="true"]{{
                background-color: {color.name()};
                border: none;
                border-radius: 8px;
                padding: 15px;
                color: #ffffff;
                font-size: 16px;
                text-align: left;
                padding-left: 20px;
                margin-bottom: 5px;
            }}
            QPushButton[animated="true"]:hover {{
                background-color: {color.name()};
            }}
            QPushButton#LogoutButton[animated="true"] {{
                background-color: {color.name()};
                font-weight: bold;
            }}
            QPushButton#LogoutButton[animated="true"]:hover {{
                background-color: {color.name()};
            }}
        """)

    def update_time_and_date(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%d %B %Y"))

    def check_unseen_tasks(self):
        has_unseen = tasks_collection.find_one({
            "username": self.current_user,
            "seen": False
        })
        self.mission_notification.setVisible(bool(has_unseen))

    def init_content_area(self):
        self.current_screen = None

    def clear_content(self):
        if self.current_screen:
            self.content_layout.removeWidget(self.current_screen)
            self.current_screen.deleteLater()
            self.current_screen = None

    def show_weekly_program(self):
        self.clear_content()
        self.current_screen = WeeklyProgramScreen(self.current_user, self)
        self.content_layout.addWidget(self.current_screen)

    def show_notes(self):
        self.clear_content()
        self.current_screen = NotesScreen(self.current_user, self)
        self.content_layout.addWidget(self.current_screen)

    def show_missions(self):
        self.clear_content()
        self.current_screen = MissionsScreen(self.current_user, self)
        self.content_layout.addWidget(self.current_screen)
        self.check_unseen_tasks()

    def show_user_management(self):
        if self.current_user == "admin":
            self.clear_content()
            self.current_screen = UserManagementScreen(self)
            self.content_layout.addWidget(self.current_screen)
        else:
            QMessageBox.warning(self, "Yetkisiz Erişim", "Bu alana erişim yetkiniz yok.")

    def lock_screen(self):
        self.login_window.username_input.clear()
        self.login_window.password_input.clear()
        self.login_window.show()
        self.hide()

    def logout(self):
        QMessageBox.information(self, "Çıkış Yapıldı", "Başarıyla çıkış yaptınız.")
        self.login_window.username_input.clear()
        self.login_window.password_input.clear()
        self.login_window.show()
        self.close()

class WeeklyProgramScreen(QWidget):
    def __init__(self, current_user, main_window_instance, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.main_window = main_window_instance
        self.init_ui()
        self.load_users_to_combo()
        self.load_tasks_into_table()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(5000) # Her 5 saniyede bir güncelleme için

    def refresh_tasks(self):
        """Veritabanından verileri yeniden yükleyerek görev tablosunu yeniler."""
        self.load_tasks_into_table()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_timer.start(5000)
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self.refresh_timer.stop()
        
    def closeEvent(self, event):
        self.refresh_timer.stop()
        super().closeEvent(event)
            
    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 16px;
            }
            QLineEdit, QComboBox {
                background-color: #2d2d44;
                border: 1px solid #3d3d5c;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QPushButton {
                background-color: #6c63ff;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a73ff;
            }
            QTabWidget::pane {
                border-top: 2px solid #3d3d5c;
                background: #1e1e2f;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background: #2d2d44;
                color: #ffffff;
                border: 1px solid #3d3d5c;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                padding: 8px 15px;
            }
            QTabBar::tab:selected {
                background: #6c63ff;
                border-color: #6c63ff;
                border-bottom-color: #6c63ff;
            }
            QTableWidget {
                background-color: #2d2d44;
                border: 1px solid #3d3d5c;
                border-radius: 5px;
                gridline-color: #3d3d5c;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3d3d5c;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #1e1e2f;
                font-weight: bold;
            }
            /* Custom checkbox images (ensure these exist in your project) */
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            /*
            QCheckBox::indicator:unchecked {
                image: url(unchecked.png);
            }
            QCheckBox::indicator:checked {
                image: url(checked.png);
            }
            */
        """)

        main_layout = QVBoxLayout()

        assignment_layout = QHBoxLayout()
        
        if self.current_user == "admin":
            assignment_layout.addWidget(QLabel("Kullanıcı:"))
            self.user_combo = QComboBox()
            self.user_combo.setMinimumWidth(150)
            assignment_layout.addWidget(self.user_combo)

            assignment_layout.addWidget(QLabel("Görev:"))
            self.task_input = QLineEdit()
            self.task_input.setPlaceholderText("Atanacak görevi girin...")
            assignment_layout.addWidget(self.task_input)

            self.assign_task_button = QPushButton("Görev Ata")
            self.assign_task_button.clicked.connect(self.assign_task)
            assignment_layout.addWidget(self.assign_task_button)

            self.delete_task_button = QPushButton("Seçili Görevi Sil")
            self.delete_task_button.clicked.connect(self.delete_selected_task)
            assignment_layout.addWidget(self.delete_task_button)

        assignment_layout.addStretch(1)

        if self.current_user == "admin":
            main_layout.addLayout(assignment_layout)
            main_layout.addSpacing(20)

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.load_tasks_into_table)

        self.days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        self.tables = {}

        for day in self.days:
            table_widget = QTableWidget()
            table_widget.setColumnCount(3)
            table_widget.setHorizontalHeaderLabels(["Kullanıcı", "Görev", "Tamamlandı"])
            table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            table_widget.setColumnWidth(2, 100)
            table_widget.setSelectionBehavior(QTableWidget.SelectRows)
            table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
            self.tables[day] = table_widget
            self.tab_widget.addTab(table_widget, day)
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def load_users_to_combo(self):
        if self.current_user == "admin":
            self.user_combo.clear()
            try:
                users = users_collection.find({})
                for user in users:
                    if user["_id"] != "admin":
                        self.user_combo.addItem(user["_id"])
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenirken hata oluştu: {e}")

    def assign_task(self):
        username = self.user_combo.currentText()
        selected_day_index = self.tab_widget.currentIndex()
        day = self.days[selected_day_index]
        task_text = self.task_input.text().strip()

        if not username or not day or not task_text:
            QMessageBox.warning(self.parent(), "Uyarı", "Lütfen tüm alanları doldurun ve bir kullanıcı seçin.")
            return

        try:
            task_doc = tasks_collection.find_one({"username": username, "day": day})

            if task_doc:
                tasks_collection.update_one(
                    {"_id": task_doc["_id"]},
                    {"$push": {"tasks": {"_id": ObjectId(), "text": task_text, "completed": False}}},
                    upsert=False
                )
            else:
                tasks_collection.insert_one({
                    "username": username,
                    "day": day,
                    "tasks": [{"_id": ObjectId(), "text": task_text, "completed": False}],
                    "seen": False
                })
            
            self.load_tasks_into_table()
            self.task_input.clear()
            QMessageBox.information(self.parent(), "Başarılı", "Görev başarıyla atandı!")
            
            if self.main_window:
                self.main_window.check_unseen_tasks()

        except Exception as e:
            QMessageBox.critical(self.parent(), "Hata", f"Görev atanırken hata oluştu: {e}")

    def delete_selected_task(self):
        selected_day = self.tab_widget.tabText(self.tab_widget.currentIndex())
        table = self.tables[selected_day]
        selected_row = table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(self.parent(), "Hata", "Lütfen silmek için bir görev seçin!")
            return

        selected_user = table.item(selected_row, 0).text()
        task_id_to_delete = table.item(selected_row, 1).data(Qt.UserRole) 

        if not task_id_to_delete:
            QMessageBox.warning(self.parent(), "Hata", "Silinecek görevin kimliği bulunamadı! (Veri yapısı uyumsuzluğu olabilir)")
            return

        reply = QMessageBox.question(self.parent(), "Onay", f"'{selected_user}' kullanıcısının '{table.item(selected_row, 1).text()}' görevini silmek istediğinizden emin misiniz?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                tasks_collection.update_one(
                    {"username": selected_user, "day": selected_day},
                    {"$pull": {"tasks": {"_id": ObjectId(task_id_to_delete)}}}
                )

                remaining_tasks_doc = tasks_collection.find_one({"username": selected_user, "day": selected_day})
                if remaining_tasks_doc and not remaining_tasks_doc.get("tasks"):
                    tasks_collection.delete_one({"_id": remaining_tasks_doc["_id"]})

                self.load_tasks_into_table()
                QMessageBox.information(self.parent(), "Başarılı", "Görev başarıyla silindi!")
                
                if self.main_window:
                    self.main_window.check_unseen_tasks()

            except Exception as e:
                QMessageBox.critical(self.parent(), "Hata", f"Bir hata oluştu: {e}")

    def load_tasks_into_table(self):
        for day_key, table in self.tables.items():
            table.setRowCount(0)
            try:
                tasks_cursor = tasks_collection.find({"day": day_key})
                row = 0
                for task_doc in tasks_cursor:
                    username = task_doc["username"]
                    tasks_list = task_doc.get("tasks", [])

                    for task_item in tasks_list:
                        table.insertRow(row)
                        
                        table.setItem(row, 0, QTableWidgetItem(username))
                        
                        task_text_item = QTableWidgetItem(task_item.get("text", "Görev Yok"))
                        task_text_item.setData(Qt.UserRole, str(task_item.get("_id")))
                        table.setItem(row, 1, task_text_item)

                        checkbox = QCheckBox()
                        is_completed = task_item.get("completed", False)
                        checkbox.setChecked(is_completed)
                        
                        if self.current_user != username:
                            checkbox.setEnabled(False)
                        
                        checkbox.stateChanged.connect(
                            lambda state, u=username, d=day_key, tid=str(task_item.get("_id")): 
                                self.toggle_task_completion(state, u, d, tid)
                        )
                        table.setCellWidget(row, 2, checkbox)
                        row += 1
            except Exception as e:
                QMessageBox.critical(self.parent(), "Hata", f"{day_key} görevleri yüklenirken hata oluştu: {e}")

    def toggle_task_completion(self, state, username, day_key, task_id):
        is_completed = bool(state == Qt.Checked)
        try:
            tasks_collection.update_one(
                {"username": username, "day": day_key, "tasks._id": ObjectId(task_id)},
                {"$set": {"tasks.$.completed": is_completed}}
            )
            print(f"Görev (ID: {task_id}) tamamlanma durumu güncellendi: {is_completed}")
        except Exception as e:
            QMessageBox.critical(self.parent(), "Hata", f"Görevin tamamlanma durumu güncellenirken hata oluştu: {e}")

class MissionsScreen(QWidget):
    def __init__(self, current_user, parent_window, parent=None):
        self.cached_task_state =""
        super().__init__(parent)
        self.username = current_user
        self.parent_window = parent_window
        self.init_ui()
        self.load_tasks(self.username)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(lambda: self.load_tasks(self.username))
        self.refresh_timer.start(3000)

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
            }
            QTableWidget {
                background-color: #2d2d44;
                border: 1px solid #3d3d5c;
                border-radius: 5px;
                gridline-color: #3d3d5c;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3d3d5c;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #1e1e2f;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QPushButton {
                background-color: #6c63ff;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                color: #ffffff;
                font-weight: bold;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #7a73ff;
            }
            /* QMessageBox Button Styling */
            QMessageBox QPushButton {
                background-color: #6c63ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #7a73ff;
            }
        """)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{self.username} İçin Görevler:"))

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Gün", "Görev", "Tamamlandı"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 100)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_tasks(self, username):
        self.table.setRowCount(0)

        try:
            tasks_cursor = tasks_collection.find({"username": username})
            row = 0
            for task_doc in tasks_cursor:
                day_key = task_doc.get("day")
                tasks_list = task_doc.get("tasks", [])
                
                for task_item in tasks_list:
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(day_key.capitalize()))
                    self.table.setItem(row, 1, QTableWidgetItem(task_item.get("text", "Görev Yok")))

                    checkbox = QCheckBox()
                    is_completed = task_item.get("completed", False)
                    checkbox.setChecked(is_completed)
                    
                    checkbox.stateChanged.connect(
                        lambda state, d=day_key, tid=str(task_item.get("_id")): self.toggle_task_completion(state, d, tid)
                    )
                    
                    self.table.setCellWidget(row, 2, checkbox)
                    row += 1
                
                if tasks_list:
                    tasks_collection.update_one(
                        {"_id": task_doc["_id"]},
                        {"$set": {"seen": True}}
                    )
            
            if self.parent_window:
                self.parent_window.check_unseen_tasks()

        except Exception as e:
            QMessageBox.warning(self.parent(), "Hata", f"Görevler yüklenirken hata oluştu: {e}")
            
    def toggle_task_completion(self, state, day_key, task_id):
        is_completed = bool(state == Qt.Checked)
        try:
            tasks_collection.update_one(
                {"username": self.username, "day": day_key, "tasks._id": ObjectId(task_id)},
                {"$set": {"tasks.$.completed": is_completed}}
            )
            print(f"Görev (ID: {task_id}) tamamlanma durumu güncellendi: {is_completed}")
        except Exception as e:
            QMessageBox.critical(self.parent(), "Hata", f"Görevin tamamlanma durumu güncellenirken hata oluştu: {e}")

class UserManagementScreen(QWidget):
    def __init__(self, main_window_instance, parent=None):
        super().__init__(parent)
        self.main_window = main_window_instance
        self.setWindowTitle("Kullanıcı Yönetimi")
        self.setGeometry(150, 150, 600, 400)
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2f; color: #e0e0e0; }
            QPushButton { background-color: #2d2d44; border: 1px solid #444; color: #e0e0e0; font-size: 16px; padding: 8px 16px; border-radius: 8px; }
            QPushButton:hover { background-color: #3d3d5c; }
            QPushButton:pressed { background-color: #50507a; }
            QLabel { color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
            QLineEdit, QTextEdit { padding: 6px 10px; border: 1px solid #555; border-radius: 8px; font-size: 16px; background-color: #2d2d44; color: #e0e0e0; }
            QLineEdit:focus, QTextEdit:focus { border: 1px solid #6c63ff; }
            QTableWidget { background-color: #2d2d44; color: #e0e0e0; border: 1px solid #555; gridline-color: #444; selection-background-color: #6c63ff; selection-color: #e0e0e0; }
            QHeaderView::section { background-color: #3d3d5c; color: #e0e0e0; padding: 5px; border: 1px solid #555; }
            /* QMessageBox Button Styling */
            QMessageBox QPushButton {
                background-color: #6c63ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #7a73ff;
            }
        """)
        self.center()
        self.init_ui()
        self.update_user_table()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.user_table = QTableWidget(0, 1)
        self.user_table.setHorizontalHeaderLabels(["Kullanıcılar"])
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)

        button_layout = QHBoxLayout()
        self.add_user_button = QPushButton("Kullanıcı Ekle")
        self.delete_user_button = QPushButton("Kullanıcı Sil")

        button_layout.addWidget(self.add_user_button)
        button_layout.addWidget(self.delete_user_button)

        main_layout.addWidget(self.user_table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.add_user_button.clicked.connect(self.add_user)
        self.delete_user_button.clicked.connect(self.delete_user)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_user_table(self):
        self.user_table.setRowCount(0)
        try:
            users = [user["_id"] for user in users_collection.find()]
            self.user_table.setRowCount(len(users))
            for i, user in enumerate(users):
                self.user_table.setItem(i, 0, QTableWidgetItem(user))
        except Exception as e:
            QMessageBox.critical(self.parent(), "Hata", f"Kullanıcı tablosu güncellenirken hata oluştu: {e}")

    def add_user(self):
        username, ok = QInputDialog.getText(self, "Kullanıcı Ekle", "Yeni kullanıcı adı:")
        if ok and username:
            password, ok = QInputDialog.getText(self, "Kullanıcı Ekle", f"{username} için şifre:", QLineEdit.Password)
            if ok and password:
                try:
                    if users_collection.find_one({"_id": username}):
                        QMessageBox.warning(self.parent(), "Uyarı", f"'{username}' kullanıcısı zaten mevcut.")
                        return
                    
                    # Şifreyi hashlerek kaydet
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                    users_collection.insert_one({
                        "_id": username,
                        "password": hashed_password.decode('utf-8'),
                        "is_first_login": True,
                        "seen": False
                    })
                    QMessageBox.information(self.parent(), "Başarılı", f"{username} kullanıcısı başarıyla eklendi!")
                    self.update_user_table()
                except Exception as e:
                    QMessageBox.warning(self.parent(), "Hata", f"Kullanıcı eklenirken hata oluştu: {e}")

    def delete_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.parent(), "Uyarı", "Lütfen silmek için bir kullanıcı seçin!")
            return

        username_to_delete = self.user_table.item(selected_row, 0).text()

        if username_to_delete == "admin":
            QMessageBox.warning(self.parent(), "Hata", "Admin kullanıcısı silinemez!")
            return
        
        if username_to_delete == self.main_window.current_user:
            QMessageBox.warning(self.parent(), "Hata", "Kendi hesabınızı silemezsiniz!")
            return

        reply = QMessageBox.question(self.parent(), "Onay", f"'{username_to_delete}' kullanıcısını silmek istediğinizden emin misiniz? Bu işlem, kullanıcıya ait tüm görev ve notları da silecektir.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                users_collection.delete_one({"_id": username_to_delete})
                tasks_collection.delete_many({"username": username_to_delete})
                notes_collection.delete_many({"username": username_to_delete})

                QMessageBox.information(self.parent(), "Başarılı", f"{username_to_delete} kullanıcısı ve tüm verileri silindi!")
                self.update_user_table()
            except Exception as e:
                QMessageBox.critical(self.parent(), "Hata", f"Kullanıcı silinirken hata oluştu: {e}")

class NotesScreen(QWidget):
    def __init__(self, username, main_window_instance, parent=None):
        super().__init__(parent)
        self.username = username
        self.main_window = main_window_instance
        self.setWindowTitle(f"{username}'in Özel Notları")
        self.setGeometry(250, 250, 800, 600)

        main_layout = QVBoxLayout()
        self.center()
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #e0e0e0;
            }
            /* QMessageBox Button Styling */
            QMessageBox QPushButton {
                background-color: #6c63ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #7a73ff;
            }
        """)

        note_input_layout = QVBoxLayout()
        self.note_title_label = QLabel("Not Başlığı (İsteğe Bağlı):")
        self.note_title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.note_title_input = QLineEdit()
        self.note_title_input.setPlaceholderText("Not başlığını girin...")
        self.note_title_input.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #555; background-color: #2d2d44; color: #e0e0e0;")

        self.note_content_label = QLabel("Not İçeriği:")
        self.note_content_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        self.note_content_input = QTextEdit()
        self.note_content_input.setPlaceholderText("Notunuzu buraya yazın...")
        self.note_content_input.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #555; background-color: #2d2d44; color: #e0e0e0;")

        self.save_note_button = QPushButton("Notu Kaydet")
        self.save_note_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_note_button.clicked.connect(self.save_note)

        note_input_layout.addWidget(self.note_title_label)
        note_input_layout.addWidget(self.note_title_input)
        note_input_layout.addWidget(self.note_content_label)
        note_input_layout.addWidget(self.note_content_input)
        note_input_layout.addWidget(self.save_note_button)
        note_input_layout.addSpacing(20)

        self.existing_notes_label = QLabel("Mevcut Notlarınız:")
        self.existing_notes_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.notes_list_widget = QListWidget()
        self.notes_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2d2d44;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #6c63ff;
                color: white;
            }
        """)
        self.notes_list_widget.itemClicked.connect(self.display_selected_note)
        self.delete_note_button = QPushButton("Seçili Notu Sil")
        self.delete_note_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.delete_note_button.clicked.connect(self.delete_selected_note)

        main_layout.addLayout(note_input_layout)
        main_layout.addWidget(self.existing_notes_label)
        main_layout.addWidget(self.notes_list_widget)
        main_layout.addWidget(self.delete_note_button)

        self.setLayout(main_layout)
        self.load_notes()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_notes(self):
        self.notes_list_widget.clear()
        try:
            user_notes = notes_collection.find({"username": self.username}).sort("timestamp", -1)
            for note in user_notes:
                item_text = note.get("title", "Başlıksız Not")
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, str(note["_id"]))
                self.notes_list_widget.addItem(list_item)
        except Exception as e:
            QMessageBox.warning(self.parent(), "Hata", f"Notlar yüklenemedi: {e}")

    def save_note(self):
        title = self.note_title_input.text().strip()
        content = self.note_content_input.toPlainText().strip()

        if not content:
            QMessageBox.warning(self.parent(), "Uyarı", "Not içeriği boş olamaz!")
            return

        try:
            note_data = {
                "username": self.username,
                "title": title if title else "Başlıksız Not",
                "content": content,
                "timestamp": datetime.now()
            }
            notes_collection.insert_one(note_data)
            QMessageBox.information(self.parent(), "Başarılı", "Not kaydedildi!")
            self.note_title_input.clear()
            self.note_content_input.clear()
            self.load_notes()
        except Exception as e:
            QMessageBox.critical(self.parent(), "Hata", f"Not kaydedilirken hata oluştu: {e}")

    def display_selected_note(self, item):
        note_id = item.data(Qt.UserRole)
        try:
            note = notes_collection.find_one({"_id": ObjectId(note_id)})
            if note:
                self.note_title_input.setText(note.get("title", ""))
                self.note_content_input.setText(note.get("content", ""))
        except Exception as e:
            QMessageBox.critical(self.parent(), "Hata", f"Not detayları yüklenirken hata oluştu: {e}")

    def delete_selected_note(self):
        selected_item = self.notes_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent(), "Uyarı", "Lütfen silmek için bir not seçin!")
            return

        reply = QMessageBox.question(self.parent(), "Onay", "Seçili notu silmek istediğinizden emin misiniz?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            note_id = selected_item.data(Qt.UserRole)
            try:
                notes_collection.delete_one({"_id": ObjectId(note_id)})
                QMessageBox.information(self.parent(), "Başarılı", "Not silindi!")
                self.note_title_input.clear()
                self.note_content_input.clear()
                self.load_notes()
            except Exception as e:
                QMessageBox.critical(self.parent(), "Hata", f"Not silinirken hata oluştu: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())