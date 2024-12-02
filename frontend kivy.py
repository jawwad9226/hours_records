from datetime import datetime
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition, CardTransition
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.button import MDFillRoundFlatIconButton, MDIconButton
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.snackbar import MDSnackbar
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
import sqlite3
import os
import platform

# Set window size to match common Android aspect ratio (16:9)
if platform != 'android':
    Window.size = (360, 640)

# Database Configuration
DB_NAME = 'work_tracker.db'

class DatabaseManager:
    @staticmethod
    def get_db_path():
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, DB_NAME)

    @staticmethod
    def connect():
        try:
            connection = sqlite3.connect(DatabaseManager.get_db_path())
            return connection
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return None

    @staticmethod
    def create_table_if_not_exists():
        try:
            connection = DatabaseManager.connect()
            if connection:
                cursor = connection.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS working_hourse (
                        sr_no INTEGER PRIMARY KEY AUTOINCREMENT,
                        date_time TIMESTAMP,
                        hourse INTEGER
                    )
                """)
                connection.commit()
                cursor.close()
                connection.close()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    @staticmethod
    def write_to_db(date_time, hours):
        try:
            connection = DatabaseManager.connect()
            if connection:
                cursor = connection.cursor()
                # Convert datetime to string in SQLite format
                date_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO working_hourse (date_time, hourse) VALUES (?, ?)",
                    (date_str, hours)
                )
                connection.commit()
                cursor.close()
                connection.close()
                return True
            return False
        except sqlite3.Error as e:
            print(f"Error writing to database: {e}")
            return False

    @staticmethod
    def read_from_db():
        try:
            connection = DatabaseManager.connect()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM working_hourse ORDER BY date_time DESC")
                records = cursor.fetchall()
                cursor.close()
                connection.close()
                
                # Convert string dates back to datetime objects
                formatted_records = []
                for record in records:
                    try:
                        date_obj = datetime.strptime(record[1], '%Y-%m-%d %H:%M:%S')
                        formatted_records.append((record[0], date_obj, record[2]))
                    except (ValueError, TypeError):
                        # If date parsing fails, use the original record
                        formatted_records.append(record)
                
                return formatted_records
            return []
        except sqlite3.Error as e:
            print(f"Error reading from database: {e}")
            return []

    @staticmethod
    def get_summary():
        try:
            connection = DatabaseManager.connect()
            if connection:
                cursor = connection.cursor()
                # Get total hours
                cursor.execute("SELECT SUM(hourse) FROM working_hourse")
                total_hours = cursor.fetchone()[0] or 0
                
                # Get today's hours
                cursor.execute(
                    "SELECT SUM(hourse) FROM working_hourse WHERE date(date_time) = date('now', 'localtime')"
                )
                today_hours = cursor.fetchone()[0] or 0
                
                # Get this month's hours
                cursor.execute(
                    "SELECT SUM(hourse) FROM working_hourse WHERE strftime('%Y-%m', date_time) = strftime('%Y-%m', 'now', 'localtime')"
                )
                month_hours = cursor.fetchone()[0] or 0
                
                cursor.close()
                connection.close()
                return today_hours, month_hours, total_hours
            return 0, 0, 0
        except sqlite3.Error as e:
            print(f"Error getting summary: {e}")
            return 0, 0, 0

class NumericSpinner(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.adaptive_size = True
        self.spacing = dp(10)
        self.size_hint_x = None
        self.width = dp(150)  # Fixed width for better layout
        self.pos_hint = {"center_x": 0.5}
        
        # Down button
        self.down_button = MDIconButton(
            icon="minus",
            on_release=self.decrease_value,
            pos_hint={"center_y": 0.5}
        )
        
        # Input field
        self.text_input = MDTextField(
            text="0",
            input_filter="int",
            size_hint_x=None,
            width=dp(60),
            halign="center",
            pos_hint={"center_y": 0.5}
        )
        
        # Up button
        self.up_button = MDIconButton(
            icon="plus",
            on_release=self.increase_value,
            pos_hint={"center_y": 0.5}
        )
        
        # Add widgets
        self.add_widget(self.down_button)
        self.add_widget(self.text_input)
        self.add_widget(self.up_button)
    
    def get_value(self):
        try:
            return int(self.text_input.text)
        except ValueError:
            return 0
    
    def set_value(self, value):
        self.text_input.text = str(max(0, value))
    
    def increase_value(self, instance):
        current = self.get_value()
        self.set_value(current + 1)
    
    def decrease_value(self, instance):
        current = self.get_value()
        self.set_value(current - 1)

class RecordScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_resize=self.on_window_resize)
        Clock.schedule_once(self.update_table, 0.5)  # Initial table load
        
    def on_enter(self):
        """Called when screen is entered"""
        self.update_table()
        
    def on_window_resize(self, instance, width, height):
        """Handle window resize events"""
        try:
            self.update_table()
        except Exception as e:
            print(f"Error handling resize: {e}")

    def update_table(self, *args):
        try:
            self.ids.records_table.clear_widgets()
            
            records = DatabaseManager.read_from_db()
            if not records:
                records = []
                
            formatted_data = []
            for row in records:
                try:
                    date_str = row[1].strftime('%d/%m %H:%M') if isinstance(row[1], datetime) else str(row[1])
                    formatted_data.append((str(row[0]), date_str, str(row[2])))
                except (AttributeError, TypeError) as e:
                    print(f"Error formatting row {row}: {e}")
                    continue
            
            # Get screen dimensions
            screen_width = Window.width
            table_width = screen_width * 0.95  # Use 95% of screen width
            
            # Calculate column widths
            col1_width = dp(40)  # ID column
            col3_width = dp(40)  # Hours column
            col2_width = table_width - col1_width - col3_width - dp(20)  # Date column with padding
            
            data_table = MDDataTable(
                size_hint=(None, None),
                width=table_width,
                height=dp(350),  # Reduced height for mobile
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                use_pagination=True,
                pagination_menu_pos="auto",
                rows_num=6,  # Reduced for better mobile view
                column_data=[
                    ("ID", col1_width),
                    ("Date", col2_width),
                    ("Hrs", col3_width)
                ],
                row_data=formatted_data,
                column_data_height=dp(40),  # Increased touch target
                row_data_height=dp(35),     # Increased touch target
            )
            
            self.ids.records_table.add_widget(data_table)
            
        except Exception as e:
            print(f"Error updating table: {e}")
            self.show_error_message("Error loading records")

    def show_error_message(self, message):
        """Show error message using red Snackbar"""
        try:
            snackbar = MDSnackbar(
                MDLabel(
                    text=message,
                    theme_text_color="Custom",
                    text_color="white",
                ),
                y=10,
                pos_hint={"center_x": 0.5},
                size_hint_x=0.9,
                md_bg_color=(0.8, 0.2, 0.2, 1),
                duration=2
            )
            snackbar.open()
        except Exception as e:
            print(f"Error showing error message: {e}")

    def go_to_home(self):
        try:
            self.manager.transition = CardTransition(direction="right", duration=0.3)
            self.manager.current = 'home'
        except Exception as e:
            print(f"Error navigating to home: {e}")

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.update_datetime, 1)  # Update time every second
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, instance, width, height):
        """Handle window resize events"""
        try:
            self.update_summary()  # Refresh the layout
        except Exception as e:
            print(f"Error handling resize: {e}")

    def update_datetime(self, dt):
        """Update the datetime label"""
        try:
            if hasattr(self.ids, 'datetime_label'):
                self.ids.datetime_label.text = self.get_current_datetime()
        except Exception as e:
            print(f"Error updating datetime: {e}")

    def animate_button(self, instance):
        try:
            anim = Animation(scale_x=0.9, scale_y=0.9, duration=0.1) + Animation(scale_x=1, scale_y=1, duration=0.1)
            anim.bind(on_complete=lambda *args: self.animation_complete(instance))
            anim.start(instance)
        except Exception as e:
            print(f"Animation error: {e}")

    def animation_complete(self, instance):
        try:
            if instance.text == "Save Record":
                self.save_record()
            elif instance.text == "View All Records":
                self.go_to_records()
        except Exception as e:
            print(f"Error in animation complete: {e}")
            self.show_error_message("An error occurred")

    def save_record(self):
        try:
            hours = self.ids.hours_input.get_value()
            if not isinstance(hours, (int, float)) or hours <= 0:
                self.show_error_message("Please enter valid hours (greater than 0)")
                return
                
            if hours > 24:
                self.show_error_message("Hours cannot exceed 24")
                return
                
            current_time = datetime.now()
            if DatabaseManager.write_to_db(current_time, hours):
                self.update_summary()
                self.ids.hours_input.set_value(0)
                self.show_success_message("Record Added Successfully!")
            else:
                self.show_error_message("Failed to add record")
        except Exception as e:
            print(f"Error saving record: {e}")
            self.show_error_message("Error saving record")

    def show_success_message(self, message):
        """Show success message using green Snackbar"""
        try:
            snackbar = MDSnackbar(
                MDLabel(
                    text=message,
                    theme_text_color="Custom",
                    text_color="white",
                ),
                y=10,
                pos_hint={"center_x": 0.5},
                size_hint_x=0.9,
                md_bg_color=(0.2, 0.8, 0.2, 1),
                duration=1.5
            )
            snackbar.open()
        except Exception as e:
            print(f"Error showing success message: {e}")

    def show_error_message(self, message):
        """Show error message using red Snackbar"""
        try:
            snackbar = MDSnackbar(
                MDLabel(
                    text=message,
                    theme_text_color="Custom",
                    text_color="white",
                ),
                y=10,
                pos_hint={"center_x": 0.5},
                size_hint_x=0.9,
                md_bg_color=(0.8, 0.2, 0.2, 1),
                duration=2
            )
            snackbar.open()
        except Exception as e:
            print(f"Error showing error message: {e}")

    def on_enter(self):
        self.ids.datetime_label.text = self.get_current_datetime()
        self.update_summary()
        
    def get_current_datetime(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_summary(self):
        total_records, total_hours, month_hours = DatabaseManager.get_summary()
        self.ids.total_records.text = f"Total Records: {total_records}"
        self.ids.total_hours.text = f"Total Hours: {total_hours}"
        self.ids.month_records.text = f"This Month: {month_hours}"

    def go_to_records(self):
        self.manager.transition = CardTransition(direction="left", duration=0.3)
        self.manager.current = 'records'

class WorkTrackerApp(MDApp):
    def build(self):
        if platform != 'android':
            Window.size = (360, 640)
        else:
            # Android-specific settings
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
            
        # Theme settings
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # Create database on first run
        DatabaseManager.create_table_if_not_exists()
        
        # Load KV string
        KV = '''
<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        padding: dp(10)

        MDTopAppBar:
            title: "Work Tracker"
            elevation: 0
            pos_hint: {"top": 1}

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(10)
                padding: dp(10)
                adaptive_height: True

                MDLabel:
                    id: datetime_label
                    halign: "center"
                    theme_text_color: "Primary"
                    font_style: "H6"

                # Hours Input Section with NumericSpinner
                MDCard:
                    orientation: "vertical"
                    padding: dp(15)
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(120)
                    md_bg_color: app.theme_cls.bg_dark

                    MDLabel:
                        text: "Enter Working Hours"
                        theme_text_color: "Primary"
                        font_style: "H6"
                        size_hint_y: None
                        height: dp(30)

                    NumericSpinner:
                        id: hours_input
                        size_hint_y: None
                        height: dp(50)
                        pos_hint: {"center_x": .5}

                MDFillRoundFlatIconButton:
                    text: "Save Record"
                    icon: "content-save"
                    size_hint_x: 0.8
                    height: dp(48)
                    pos_hint: {"center_x": .5}
                    scale_x: 1
                    scale_y: 1
                    on_release: 
                        root.animate_button(self)

                # Summary Section
                MDCard:
                    orientation: "vertical"
                    padding: dp(15)
                    spacing: dp(5)
                    size_hint_y: None
                    height: dp(150)
                    md_bg_color: app.theme_cls.bg_dark

                    MDLabel:
                        text: "Summary"
                        theme_text_color: "Primary"
                        font_style: "H6"

                    GridLayout:
                        cols: 2
                        spacing: dp(10)
                        padding: dp(10)

                        MDLabel:
                            text: "Total Records:"
                            theme_text_color: "Secondary"
                        MDLabel:
                            id: total_records
                            text: "0"
                            theme_text_color: "Primary"

                        MDLabel:
                            text: "Total Hours:"
                            theme_text_color: "Secondary"
                        MDLabel:
                            id: total_hours
                            text: "0"
                            theme_text_color: "Primary"

                        MDLabel:
                            text: "This Month:"
                            theme_text_color: "Secondary"
                        MDLabel:
                            id: month_records
                            text: "0"
                            theme_text_color: "Primary"

                MDFillRoundFlatIconButton:
                    text: "View All Records"
                    icon: "database"
                    size_hint_x: 0.8
                    height: dp(48)
                    pos_hint: {"center_x": .5}
                    scale_x: 1
                    scale_y: 1
                    on_release: 
                        root.animate_button(self)

<RecordScreen>:
    BoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        padding: dp(10)

        MDTopAppBar:
            title: "Records"
            elevation: 0
            left_action_items: [["arrow-left", lambda x: root.go_to_home()]]

        BoxLayout:
            id: records_table
            orientation: "vertical"
            padding: dp(5)
            
        MDLabel:
            text: "Made by: SJAM Creates"
            theme_text_color: "Secondary"
            halign: "center"
            size_hint_y: None
            height: dp(30)
            font_style: "Caption"
'''
        Builder.load_string(KV)
        
        # Create screen manager with smooth transition
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(RecordScreen(name="records"))
        return sm

    def is_android(self):
        try:
            from android.permissions import request_permissions, Permission
            return True
        except ImportError:
            return False
            
    def on_start(self):
        """Called when the application starts."""
        try:
            DatabaseManager.create_table_if_not_exists()
            conn = DatabaseManager.connect()
            if conn:
                conn.close()
            else:
                snackbar = MDSnackbar(
                    MDLabel(
                        text="Database connection failed",
                        theme_text_color="Custom",
                        text_color="white",
                    ),
                    y=10,
                    pos_hint={"center_x": 0.5},
                    size_hint_x=0.9,
                    md_bg_color=(0.8, 0.2, 0.2, 1),
                    duration=2
                )
                snackbar.open()
        except Exception as e:
            print(f"Error during app start: {e}")

if __name__ == '__main__':
    try:
        if platform == 'android':
            from android.storage import primary_external_storage_path
            dir_path = primary_external_storage_path()
            DatabaseManager.DB_PATH = os.path.join(dir_path, 'work_tracker.db')
        
        WorkTrackerApp().run()
    except Exception as e:
        print(f"Application Error: {e}")
